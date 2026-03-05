"""
TDD测试 — response模块
使用socketpair()构造真实socket对进行测试
"""
import socket
import sys
import os
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.response import (
    send_ok_headers, send_bad_request, send_not_found,
    send_cannot_execute, send_unimplemented, SERVER_STRING
)


def make_pair():
    a, b = socket.socketpair()
    return a, b


def recv_all(sock, timeout=0.3):
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass
    return data


class TestSendOkHeaders(unittest.TestCase):
    def test_starts_with_200(self):
        w, r = make_pair()
        send_ok_headers(w); w.close()
        data = recv_all(r); r.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 200 OK\r\n"))

    def test_contains_server_string(self):
        w, r = make_pair()
        send_ok_headers(w); w.close()
        data = recv_all(r); r.close()
        self.assertIn(SERVER_STRING, data)

    def test_contains_content_type_html(self):
        w, r = make_pair()
        send_ok_headers(w); w.close()
        data = recv_all(r); r.close()
        self.assertIn(b"Content-Type: text/html\r\n", data)

    def test_ends_with_blank_line(self):
        w, r = make_pair()
        send_ok_headers(w); w.close()
        data = recv_all(r); r.close()
        self.assertIn(b"\r\n\r\n", data)

    def test_all_lines_crlf(self):
        w, r = make_pair()
        send_ok_headers(w); w.close()
        data = recv_all(r); r.close()
        # 去掉最后的\r\n\r\n后检查每行
        parts = data.split(b"\r\n")
        for part in parts:
            self.assertNotIn(b"\n", part, f"裸\\n in: {part!r}")


class TestSendBadRequest(unittest.TestCase):
    def test_starts_with_400(self):
        w, r = make_pair()
        send_bad_request(w); w.close()
        data = recv_all(r); r.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 400 BAD REQUEST\r\n"))

    def test_has_body_content(self):
        w, r = make_pair()
        send_bad_request(w); w.close()
        data = recv_all(r); r.close()
        self.assertGreater(len(data), 60)


class TestSendNotFound(unittest.TestCase):
    def test_starts_with_404(self):
        w, r = make_pair()
        send_not_found(w); w.close()
        data = recv_all(r); r.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 404 NOT FOUND\r\n"))

    def test_has_html_body(self):
        w, r = make_pair()
        send_not_found(w); w.close()
        data = recv_all(r); r.close()
        self.assertIn(b"<HTML>", data)


class TestSendCannotExecute(unittest.TestCase):
    def test_starts_with_500(self):
        w, r = make_pair()
        send_cannot_execute(w); w.close()
        data = recv_all(r); r.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 500 Internal Server Error\r\n"))


class TestSendUnimplemented(unittest.TestCase):
    def test_starts_with_501(self):
        w, r = make_pair()
        send_unimplemented(w); w.close()
        data = recv_all(r); r.close()
        self.assertTrue(data.startswith(b"HTTP/1.0 501 Method Not Implemented\r\n"))

    def test_has_html_body(self):
        w, r = make_pair()
        send_unimplemented(w); w.close()
        data = recv_all(r); r.close()
        self.assertIn(b"<HTML>", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
