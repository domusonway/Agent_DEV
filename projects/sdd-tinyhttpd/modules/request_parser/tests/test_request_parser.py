"""
TDD测试 — request_parser模块
"""
import socket
import sys
import os
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.request_parser import get_line, parse_request_line, consume_headers


def feed_socket(data: bytes):
    """创建socketpair，将data写入一端，返回另一端供读取"""
    a, b = socket.socketpair()
    a.sendall(data)
    a.close()
    return b


class TestGetLine(unittest.TestCase):
    def test_crlf_normalized_to_lf(self):
        sock = feed_socket(b"GET / HTTP/1.0\r\n")
        result = get_line(sock)
        sock.close()
        self.assertEqual(result, "GET / HTTP/1.0\n")

    def test_lf_only(self):
        sock = feed_socket(b"GET / HTTP/1.0\n")
        result = get_line(sock)
        sock.close()
        self.assertEqual(result, "GET / HTTP/1.0\n")

    def test_empty_line_crlf(self):
        sock = feed_socket(b"\r\n")
        result = get_line(sock)
        sock.close()
        self.assertEqual(result, "\n")

    def test_closed_connection_returns_empty(self):
        a, b = socket.socketpair()
        a.close()
        result = get_line(b)
        b.close()
        self.assertEqual(result, "")

    def test_multiple_lines(self):
        sock = feed_socket(b"line1\r\nline2\r\n")
        l1 = get_line(sock)
        l2 = get_line(sock)
        sock.close()
        self.assertEqual(l1, "line1\n")
        self.assertEqual(l2, "line2\n")


class TestParseRequestLine(unittest.TestCase):
    def test_get_request(self):
        method, url, proto = parse_request_line("GET /index.html HTTP/1.0\n")
        self.assertEqual(method, "GET")
        self.assertEqual(url, "/index.html")
        self.assertEqual(proto, "HTTP/1.0")

    def test_post_request(self):
        method, url, proto = parse_request_line("POST /cgi-bin/form.cgi HTTP/1.0\n")
        self.assertEqual(method, "POST")
        self.assertEqual(url, "/cgi-bin/form.cgi")

    def test_method_uppercased(self):
        method, url, proto = parse_request_line("get /path HTTP/1.0\n")
        self.assertEqual(method, "GET")

    def test_url_with_query_string(self):
        method, url, proto = parse_request_line("GET /cgi-bin/test.cgi?color=red HTTP/1.0\n")
        self.assertEqual(url, "/cgi-bin/test.cgi?color=red")

    def test_invalid_line_raises(self):
        with self.assertRaises(ValueError):
            parse_request_line("BADREQUEST\n")

    def test_root_url(self):
        method, url, proto = parse_request_line("GET / HTTP/1.0\n")
        self.assertEqual(url, "/")


class TestConsumeHeaders(unittest.TestCase):
    def test_basic_headers(self):
        raw = b"Host: localhost\r\nContent-Type: text/html\r\n\r\n"
        sock = feed_socket(raw)
        headers = consume_headers(sock)
        sock.close()
        self.assertEqual(headers.get('host'), 'localhost')
        self.assertEqual(headers.get('content-type'), 'text/html')

    def test_empty_headers(self):
        sock = feed_socket(b"\r\n")
        headers = consume_headers(sock)
        sock.close()
        self.assertEqual(headers, {})

    def test_content_length_extracted(self):
        raw = b"Content-Length: 42\r\nHost: localhost\r\n\r\n"
        sock = feed_socket(raw)
        headers = consume_headers(sock)
        sock.close()
        self.assertEqual(headers.get('content-length'), '42')

    def test_header_names_lowercased(self):
        sock = feed_socket(b"X-Custom-Header: value\r\n\r\n")
        headers = consume_headers(sock)
        sock.close()
        self.assertIn('x-custom-header', headers)


if __name__ == '__main__':
    unittest.main(verbosity=2)
