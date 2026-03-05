"""
tests/validators/validate_server_e2e.py
端到端集成测试：启动真实HTTP服务器，用socket模拟客户端验证完整请求-响应

这是SDD框架验证的关键测试：各模块单独通过后，集成层是否也正确。
"""
import io, os, socket, stat, sys, tempfile, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def send_request(host: str, port: int, raw_request: bytes, timeout: float = 3.0) -> bytes:
    """发送原始HTTP请求，返回完整响应bytes"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect((host, port))
        client.sendall(raw_request)
        # 关闭写端，触发服务器读到EOF
        client.shutdown(socket.SHUT_WR)
        buf = b""
        try:
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                buf += chunk
        except (socket.timeout, ConnectionResetError, OSError):
            pass
    return buf


def run_server_in_thread(htdocs_dir: str):
    """在临时目录中启动服务器，返回(thread, port, stop_event)"""
    from modules.server.server import startup, accept_request

    # 切换工作目录到htdocs父目录（服务器依赖相对路径）
    old_cwd = os.getcwd()
    os.chdir(htdocs_dir)

    server_sock, port = startup(0)
    server_sock.settimeout(2.0)
    stop_event = threading.Event()

    def _serve():
        while not stop_event.is_set():
            try:
                conn, addr = server_sock.accept()
                t = threading.Thread(target=accept_request, args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break
        server_sock.close()
        os.chdir(old_cwd)

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    time.sleep(0.1)  # 等待服务器就绪
    return t, port, stop_event


def main():
    print("=" * 50)
    print("E2E集成测试: server")
    print("=" * 50)

    errs = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # 准备 htdocs 目录结构
        htdocs = Path(tmpdir) / "htdocs"
        htdocs.mkdir()

        # 静态文件
        (htdocs / "index.html").write_bytes(b"<html><body>Hello Tinyhttpd</body></html>\n")
        (htdocs / "about.html").write_bytes(b"<html><body>About</body></html>\n")

        # CGI脚本
        cgi_script = htdocs / "hello.cgi"
        cgi_script.write_text(
            "#!/bin/sh\n"
            "echo 'Content-Type: text/plain'\n"
            "echo ''\n"
            "echo \"Method: $REQUEST_METHOD\"\n"
            "echo \"Query: $QUERY_STRING\"\n"
        )
        cgi_script.chmod(0o755)

        # POST CGI脚本（用python3读stdin，避免dd的块边界问题）
        post_cgi = htdocs / "echo.cgi"
        post_cgi.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "cl = int(os.environ.get('CONTENT_LENGTH', '0'))\n"
            "body = sys.stdin.buffer.read(cl)\n"
            "sys.stdout.buffer.write(b'Content-Type: text/plain\\r\\n\\r\\n')\n"
            "sys.stdout.buffer.write(body)\n"
            "sys.stdout.buffer.flush()\n"
        )
        post_cgi.chmod(0o755)

        # 启动服务器
        thread, port, stop_event = run_server_in_thread(tmpdir)

        try:
            HOST = "127.0.0.1"

            # ── 测试1：GET 静态文件 ─────────────────────────────────
            resp = send_request(HOST, port, b"GET /index.html HTTP/1.0\r\n\r\n")
            if not resp.startswith(b"HTTP/1.0 200 OK"):
                errs.append(f"T1 GET静态文件: 期望200，实际: {resp[:50]!r}")
            elif b"Hello Tinyhttpd" not in resp:
                errs.append(f"T1 GET静态文件: 响应体缺少文件内容，实际: {resp[-100:]!r}")
            else:
                print("  ✅ T1: GET /index.html → 200 + 文件内容")

            # ── 测试2：GET 不存在文件 → 404 ───────────────────────
            resp = send_request(HOST, port, b"GET /notexist.html HTTP/1.0\r\n\r\n")
            if not resp.startswith(b"HTTP/1.0 404"):
                errs.append(f"T2 GET不存在: 期望404，实际: {resp[:50]!r}")
            else:
                print("  ✅ T2: GET /notexist.html → 404")

            # ── 测试3：GET 根路径 → index.html ────────────────────
            resp = send_request(HOST, port, b"GET / HTTP/1.0\r\n\r\n")
            if not resp.startswith(b"HTTP/1.0 200 OK"):
                errs.append(f"T3 GET /: 期望200，实际: {resp[:50]!r}")
            else:
                print("  ✅ T3: GET / → 200 (index.html)")

            # ── 测试4：不支持方法 → 501 ────────────────────────────
            resp = send_request(HOST, port, b"DELETE /index.html HTTP/1.0\r\n\r\n")
            if not resp.startswith(b"HTTP/1.0 501"):
                errs.append(f"T4 DELETE方法: 期望501，实际: {resp[:50]!r}")
            else:
                print("  ✅ T4: DELETE → 501 Method Not Implemented")

            # ── 测试5：GET with query string → CGI ────────────────
            resp = send_request(HOST, port, b"GET /hello.cgi?name=world HTTP/1.0\r\n\r\n")
            if not resp.startswith(b"HTTP/1.0 200 OK"):
                errs.append(f"T5 GET CGI(query): 期望200，实际: {resp[:50]!r}")
            elif b"QUERY_STRING" not in resp and b"name=world" not in resp:
                errs.append(f"T5 GET CGI(query): CGI输出缺少QUERY_STRING，实际: {resp!r}")
            else:
                print("  ✅ T5: GET /hello.cgi?name=world → 200 + CGI输出")

            # ── 测试6：POST 无Content-Length → 400 ────────────────
            resp = send_request(
                HOST, port,
                b"POST /echo.cgi HTTP/1.0\r\n\r\n"
            )
            if not resp.startswith(b"HTTP/1.0 400"):
                errs.append(f"T6 POST无Content-Length: 期望400，实际: {resp[:50]!r}")
            else:
                print("  ✅ T6: POST 无Content-Length → 400 Bad Request")

            # ── 测试7：POST with body → CGI stdin ─────────────────
            body = b"hello_post_body"
            req = (
                b"POST /echo.cgi HTTP/1.0\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"\r\n" + body
            )
            resp = send_request(HOST, port, req)
            if not resp.startswith(b"HTTP/1.0 200 OK"):
                errs.append(f"T7 POST CGI: 期望200，实际: {resp[:50]!r}")
            elif body not in resp:
                errs.append(f"T7 POST CGI: body未传入CGI stdin，响应: {resp!r}")
            else:
                print("  ✅ T7: POST /echo.cgi → 200 + body回显")

            # ── 测试8：路径穿越防护 ────────────────────────────────
            resp = send_request(HOST, port, b"GET /../etc/passwd HTTP/1.0\r\n\r\n")
            if resp.startswith(b"HTTP/1.0 200"):
                errs.append(f"T8 路径穿越: 不应返回200，实际: {resp[:80]!r}")
            else:
                print("  ✅ T8: GET /../etc/passwd → 非200（路径穿越防护）")

            # ── 测试9：Response headers 格式校验 ──────────────────
            resp = send_request(HOST, port, b"GET /index.html HTTP/1.0\r\n\r\n")
            if b"Server: jdbhttpd/0.1.0\r\n" not in resp:
                errs.append(f"T9 Server头: 期望'Server: jdbhttpd/0.1.0'，实际: {resp[:200]!r}")
            else:
                print("  ✅ T9: Server响应头包含正确标识")

        finally:
            stop_event.set()
            thread.join(timeout=3.0)

    print()
    if not errs:
        print(f"✅ 通过 — 全部9项E2E测试通过")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
