"""
modules/server/tests/test_server.py
使用真实socket对进行集成测试
"""
import sys, os, io, socket, threading, time, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.server.server import startup, accept_request


def start_test_server(htdocs_dir: str) -> tuple:
    """启动测试服务器，返回(server_sock, port, htdocs_dir)"""
    orig_dir = os.getcwd()
    os.chdir(htdocs_dir)
    server_sock, port = startup(0)  # port=0自动分配
    return server_sock, port, orig_dir


class TestStartup(unittest.TestCase):
    def test_returns_socket_and_port(self):
        sock, port = startup(0)
        self.assertIsInstance(sock, socket.socket)
        self.assertGreater(port, 0)
        sock.close()

    def test_port_is_listening(self):
        sock, port = startup(0)
        # 能连接说明在监听
        client = socket.create_connection(("127.0.0.1", port), timeout=2)
        client.close()
        sock.close()


class TestAcceptRequest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.htdocs = os.path.join(self.tmpdir, "htdocs")
        os.makedirs(self.htdocs)
        with open(os.path.join(self.htdocs, "index.html"), "wb") as f:
            f.write(b"<html>Hello</html>")
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        import shutil
        shutil.rmtree(self.tmpdir)

    def _one_shot(self, raw: bytes) -> bytes:
        """启动服务器处理单个请求并返回响应"""
        server_sock, port = startup(0)

        def handle_one():
            try:
                server_sock.settimeout(3)
                conn, addr = server_sock.accept()
                accept_request(conn, addr)
            except Exception:
                pass
            finally:
                server_sock.close()

        t = threading.Thread(target=handle_one, daemon=True)
        t.start()
        time.sleep(0.05)  # 等待server就绪

        client = socket.create_connection(("127.0.0.1", port), timeout=3)
        client.sendall(raw)
        client.shutdown(socket.SHUT_WR)
        response = b""
        client.settimeout(3)
        try:
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk
        except (socket.timeout, ConnectionResetError):
            pass
        client.close()
        t.join(timeout=3)
        return response

    def test_get_existing_file(self):
        resp = self._one_shot(b"GET /index.html HTTP/1.0\r\n\r\n")
        self.assertTrue(resp.startswith(b"HTTP/1.0 200 OK"),
            f"应返回200，实际: {resp[:80]}")
        self.assertIn(b"<html>Hello</html>", resp)

    def test_get_nonexistent_returns_404(self):
        resp = self._one_shot(b"GET /notfound.html HTTP/1.0\r\n\r\n")
        self.assertTrue(resp.startswith(b"HTTP/1.0 404"),
            f"应返回404，实际: {resp[:80]}")

    def test_unsupported_method_returns_501(self):
        resp = self._one_shot(b"DELETE /index.html HTTP/1.0\r\n\r\n")
        self.assertTrue(resp.startswith(b"HTTP/1.0 501"),
            f"应返回501，实际: {resp[:80]}")

    def test_post_without_content_length_returns_400(self):
        resp = self._one_shot(b"POST /index.html HTTP/1.0\r\n\r\n")
        self.assertTrue(resp.startswith(b"HTTP/1.0 400"),
            f"POST无Content-Length应返回400，实际: {resp[:80]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
