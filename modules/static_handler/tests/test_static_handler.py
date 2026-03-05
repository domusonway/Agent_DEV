"""
modules/static_handler/tests/test_static_handler.py
使用MockSocket捕获sendall内容
"""
import sys, os, io, unittest, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.static_handler.static_handler import serve_file


class MockSocket:
    """捕获所有sendall的bytes"""
    def __init__(self):
        self._buf = io.BytesIO()

    def sendall(self, data: bytes):
        self._buf.write(data)

    @property
    def received(self) -> bytes:
        return self._buf.getvalue()


class TestServeFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_file(self, name: str, content: bytes) -> str:
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            f.write(content)
        return path

    def test_serve_html_file(self):
        content = b"<html><body>Hello World</body></html>\n"
        path = self._write_file("index.html", content)
        sock = MockSocket()
        serve_file(sock, path)
        data = sock.received
        # 响应以200 OK开头
        self.assertTrue(data.startswith(b"HTTP/1.0 200 OK\r\n"),
            f"响应不以200开头: {data[:50]}")
        # 响应包含文件内容
        self.assertIn(content, data, "响应不含文件内容")

    def test_serve_returns_complete_content(self):
        content = b"A" * 3000  # 超过1024块大小
        path = self._write_file("big.html", content)
        sock = MockSocket()
        serve_file(sock, path)
        self.assertIn(content, sock.received)

    def test_serve_empty_file(self):
        path = self._write_file("empty.html", b"")
        sock = MockSocket()
        serve_file(sock, path)
        data = sock.received
        self.assertTrue(data.startswith(b"HTTP/1.0 200 OK\r\n"))
        # body为空，但头部存在
        self.assertIn(b"\r\n\r\n", data)

    def test_serve_nonexistent_returns_404(self):
        sock = MockSocket()
        serve_file(sock, "/nonexistent/path/file.html")
        data = sock.received
        self.assertTrue(data.startswith(b"HTTP/1.0 404"),
            f"不存在文件应返回404，实际: {data[:50]}")

    def test_response_headers_use_crlf(self):
        content = b"test content"
        path = self._write_file("test.html", content)
        sock = MockSocket()
        serve_file(sock, path)
        data = sock.received
        # 找到头部结束前的内容
        header_end = data.index(b"\r\n\r\n")
        headers = data[:header_end]
        # 确认头部行用\r\n分隔
        self.assertIn(b"\r\n", headers)
        self.assertNotIn(b"\r\n\r\n", headers)  # 头部内不应有双空行

    def test_binary_file_served_intact(self):
        """二进制文件应原样传输，不做decode"""
        content = bytes(range(256))
        path = self._write_file("binary.bin", content)
        sock = MockSocket()
        serve_file(sock, path)
        self.assertIn(content, sock.received)


if __name__ == "__main__":
    unittest.main(verbosity=2)
