"""
modules/request_parser/tests/test_request_parser.py
使用MockSocket模拟socket.recv()行为
"""
import sys, io, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.request_parser.request_parser import get_line, parse_request_line, drain_headers, parse_content_length


class MockSocket:
    """模拟socket：从bytes流逐字节recv"""
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    def recv(self, n: int, flags: int = 0) -> bytes:
        return self._buf.read(n)


class TestGetLine(unittest.TestCase):
    def test_crlf_normalized(self):
        sock = MockSocket(b"Hello World\r\n")
        line = get_line(sock)
        self.assertEqual(line, "Hello World\n")

    def test_lf_only(self):
        sock = MockSocket(b"Hello\n")
        line = get_line(sock)
        self.assertEqual(line, "Hello\n")

    def test_empty_line(self):
        """空行（只有\r\n）→ "\n" """
        sock = MockSocket(b"\r\n")
        line = get_line(sock)
        self.assertEqual(line, "\n")

    def test_connection_close(self):
        """连接关闭（空流）→ "" """
        sock = MockSocket(b"")
        line = get_line(sock)
        self.assertEqual(line, "")

    def test_multiple_lines(self):
        """多行：每次get_line只读一行"""
        sock = MockSocket(b"first\r\nsecond\r\n")
        self.assertEqual(get_line(sock), "first\n")
        self.assertEqual(get_line(sock), "second\n")


class TestParseRequestLine(unittest.TestCase):
    def test_get_simple(self):
        sock = MockSocket(b"GET /index.html HTTP/1.0\r\n")
        result = parse_request_line(sock)
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["url"], "/index.html")
        self.assertEqual(result["query_string"], "")

    def test_get_with_query(self):
        sock = MockSocket(b"GET /cgi?name=foo&bar=1 HTTP/1.0\r\n")
        result = parse_request_line(sock)
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["url"], "/cgi")
        self.assertEqual(result["query_string"], "name=foo&bar=1")

    def test_post(self):
        sock = MockSocket(b"POST /submit HTTP/1.0\r\n")
        result = parse_request_line(sock)
        self.assertEqual(result["method"], "POST")
        self.assertEqual(result["url"], "/submit")
        self.assertEqual(result["query_string"], "")

    def test_get_root(self):
        sock = MockSocket(b"GET / HTTP/1.0\r\n")
        result = parse_request_line(sock)
        self.assertEqual(result["url"], "/")
        self.assertEqual(result["query_string"], "")

    def test_method_uppercase(self):
        sock = MockSocket(b"get /index.html HTTP/1.0\r\n")
        result = parse_request_line(sock)
        self.assertEqual(result["method"], "GET")


class TestDrainHeaders(unittest.TestCase):
    def test_drains_until_empty_line(self):
        """drain_headers消耗头部直到空行，不抛异常"""
        data = b"Content-Type: text/plain\r\nAccept: */*\r\n\r\n"
        sock = MockSocket(data)
        drain_headers(sock)  # 不应抛出异常

    def test_empty_headers(self):
        """直接空行（无头部）也正常"""
        sock = MockSocket(b"\r\n")
        drain_headers(sock)


class TestParseContentLength(unittest.TestCase):
    def test_found(self):
        data = b"Content-Type: text/plain\r\nContent-Length: 42\r\n\r\n"
        sock = MockSocket(data)
        cl = parse_content_length(sock)
        self.assertEqual(cl, 42)

    def test_not_found(self):
        data = b"Content-Type: text/plain\r\n\r\n"
        sock = MockSocket(data)
        cl = parse_content_length(sock)
        self.assertEqual(cl, -1)

    def test_case_insensitive(self):
        data = b"content-length: 100\r\n\r\n"
        sock = MockSocket(data)
        cl = parse_content_length(sock)
        self.assertEqual(cl, 100)

    def test_zero_length(self):
        data = b"Content-Length: 0\r\n\r\n"
        sock = MockSocket(data)
        cl = parse_content_length(sock)
        self.assertEqual(cl, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
