"""
tests/validators/validate_static_handler.py
校验 static_handler 模块：服务静态文件，响应与fixture基准一致
"""
import io, os, pickle, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

MODULE_NAME = "static_handler"
FIXTURES = Path(__file__).parent.parent / "fixtures"


class MockConn:
    """模拟socket连接：收集sendall写入的数据"""
    def __init__(self):
        self._buf = io.BytesIO()

    def sendall(self, data: bytes) -> None:
        self._buf.write(data)

    def getvalue(self) -> bytes:
        return self._buf.getvalue()


def main():
    print(f"{'='*50}\n校验器: {MODULE_NAME}\n{'='*50}")

    ref = pickle.loads((FIXTURES / f"reference_{MODULE_NAME}_output.pkl").read_bytes())
    test_content = ref["test_content"]
    expected_response = ref["expected_response"]
    ok_headers = ref["ok_headers"]

    from modules.static_handler.static_handler import serve_file

    errs = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = Path(tmpdir) / "test.html"
        test_file.write_bytes(test_content)

        # 测试1：正常文件服务
        conn = MockConn()
        serve_file(conn, str(test_file))
        actual = conn.getvalue()
        if actual != expected_response:
            errs.append(
                f"正常文件响应不匹配\n"
                f"  期望({len(expected_response)}B): {expected_response[:80]!r}\n"
                f"  实际({len(actual)}B): {actual[:80]!r}"
            )

        # 测试2：文件不存在 → 404
        conn2 = MockConn()
        serve_file(conn2, str(Path(tmpdir) / "nonexistent.html"))
        actual2 = conn2.getvalue()
        if not actual2.startswith(b"HTTP/1.0 404"):
            errs.append(f"不存在文件应返回404，实际: {actual2[:40]!r}")

        # 测试3：响应头使用\\r\\n
        if b"\r\n" not in actual:
            errs.append("响应头缺少\\r\\n行分隔符")

        # 测试4：响应包含200 OK
        if not actual.startswith(b"HTTP/1.0 200 OK"):
            errs.append(f"响应应以HTTP/1.0 200 OK开头，实际: {actual[:30]!r}")

    if not errs:
        print("✅ 通过 — 静态文件服务输出与基准一致")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
