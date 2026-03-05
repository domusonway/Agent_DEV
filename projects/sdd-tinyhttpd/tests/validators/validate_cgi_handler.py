"""
tests/validators/validate_cgi_handler.py
校验 cgi_handler 模块：CGI执行行为与fixture基准一致
"""
import io, os, pickle, stat, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

MODULE_NAME = "cgi_handler"
FIXTURES = Path(__file__).parent.parent / "fixtures"


class MockConn:
    def __init__(self):
        self._buf = io.BytesIO()

    def sendall(self, data: bytes) -> None:
        self._buf.write(data)

    def getvalue(self) -> bytes:
        return self._buf.getvalue()


def make_cgi_script(tmpdir: str, content: str) -> str:
    """创建可执行CGI脚本，返回路径"""
    script = Path(tmpdir) / "test.cgi"
    script.write_text(content)
    script.chmod(0o755)
    return str(script)


def main():
    print(f"{'='*50}\n校验器: {MODULE_NAME}\n{'='*50}")

    ref = pickle.loads((FIXTURES / f"reference_{MODULE_NAME}_output.pkl").read_bytes())
    cgi_output_prefix = ref["cgi_output_prefix"]
    env_keys_get = ref["env_keys_get"]
    env_keys_post = ref["env_keys_post"]

    from modules.cgi_handler.cgi_handler import execute_cgi

    errs = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试1：GET请求 → 响应以200开头
        script = make_cgi_script(
            tmpdir,
            "#!/bin/sh\necho 'Content-Type: text/plain'\necho ''\necho 'Hello CGI'"
        )
        conn = MockConn()
        execute_cgi(conn, script, "GET", "q=test")
        actual = conn.getvalue()
        if not actual.startswith(cgi_output_prefix):
            errs.append(
                f"GET CGI响应应以{cgi_output_prefix!r}开头，"
                f"实际: {actual[:50]!r}"
            )

        # 测试2：GET请求设置QUERY_STRING和REQUEST_METHOD环境变量
        env_capture_script = make_cgi_script(
            tmpdir,
            "#!/bin/sh\n"
            "echo 'REQUEST_METHOD='$REQUEST_METHOD\n"
            "echo 'QUERY_STRING='$QUERY_STRING\n"
        )
        conn2 = MockConn()
        execute_cgi(conn2, env_capture_script, "GET", "myquery=1")
        output = conn2.getvalue().decode("utf-8", errors="replace")
        if "REQUEST_METHOD=GET" not in output:
            errs.append(f"GET CGI缺少REQUEST_METHOD=GET，输出: {output!r}")
        if "QUERY_STRING=myquery=1" not in output:
            errs.append(f"GET CGI缺少QUERY_STRING=myquery=1，输出: {output!r}")

        # 测试3：POST请求设置CONTENT_LENGTH
        post_env_script = make_cgi_script(
            tmpdir,
            "#!/bin/sh\n"
            "echo 'REQUEST_METHOD='$REQUEST_METHOD\n"
            "echo 'CONTENT_LENGTH='$CONTENT_LENGTH\n"
        )
        conn3 = MockConn()
        body = b"name=world"
        execute_cgi(conn3, post_env_script, "POST", "", body)
        output3 = conn3.getvalue().decode("utf-8", errors="replace")
        if "REQUEST_METHOD=POST" not in output3:
            errs.append(f"POST CGI缺少REQUEST_METHOD=POST，输出: {output3!r}")
        if f"CONTENT_LENGTH={len(body)}" not in output3:
            errs.append(f"POST CGI缺少CONTENT_LENGTH={len(body)}，输出: {output3!r}")

        # 测试4：不可执行脚本 → 500
        bad_script = Path(tmpdir) / "bad.cgi"
        bad_script.write_text("#!/bin/sh\necho hello")
        bad_script.chmod(0o644)  # 无执行权限
        conn4 = MockConn()
        execute_cgi(conn4, str(bad_script), "GET", "")
        actual4 = conn4.getvalue()
        if not actual4.startswith(b"HTTP/1.0 500"):
            errs.append(f"不可执行脚本应返回500，实际: {actual4[:50]!r}")

        # 测试5：POST body通过stdin传入
        stdin_script = make_cgi_script(
            tmpdir,
            "#!/bin/sh\nread line\necho $line"
        )
        conn5 = MockConn()
        execute_cgi(conn5, stdin_script, "POST", "", b"hello_from_post")
        output5 = conn5.getvalue().decode("utf-8", errors="replace")
        if "hello_from_post" not in output5:
            errs.append(f"POST body未通过stdin传入CGI，输出: {output5!r}")

    if not errs:
        print("✅ 通过 — CGI执行行为与基准一致")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
