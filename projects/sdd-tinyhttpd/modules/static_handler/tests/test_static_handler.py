"""TDD测试 — static_handler模块"""
import socket
import sys
import os
import tempfile
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.static_handler import serve_file, cat_file


def make_client_with_headers(extra_headers=b""):
    """创建带有HTTP头部（以空行结尾）的socket对"""
    a, b = socket.socketpair()
    # 写入假的请求头（serve_file会消耗它们）
    a.sendall(b"Host: localhost\r\n" + extra_headers + b"\r\n")
    a.close()
    return b  # 这是client端（serve_file写入端）


def recv_all(sock, timeout=0.5):
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


class TestCatFile(unittest.TestCase):
    def test_sends_file_content(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            f.write(b"<html><body>Hello World</body></html>")
            path = f.name
        try:
            w, r = socket.socketpair()
            cat_file(w, path)
            w.close()
            data = recv_all(r)
            r.close()
            self.assertIn(b"Hello World", data)
        finally:
            os.unlink(path)

    def test_sends_large_file_completely(self):
        content = b"X" * 5000  # 超过1024的CHUNK_SIZE
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            path = f.name
        try:
            w, r = socket.socketpair()
            cat_file(w, path)
            w.close()
            data = recv_all(r)
            r.close()
            self.assertEqual(len(data), 5000)
        finally:
            os.unlink(path)


class TestServeFile(unittest.TestCase):
    def test_existing_file_returns_200(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            f.write(b"<h1>Test Page</h1>")
            path = f.name
        try:
            # socketpair: a=client端(serve_file的target), b=test读取端
            a, b = socket.socketpair()
            # 给a写入要消耗的请求头
            b.sendall(b"Host: localhost\r\n\r\n")
            serve_file(a, path)
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(b"HTTP/1.0 200 OK", data)
            self.assertIn(b"<h1>Test Page</h1>", data)
        finally:
            os.unlink(path)

    def test_nonexistent_file_returns_404(self):
        a, b = socket.socketpair()
        b.sendall(b"\r\n")  # 空headers
        serve_file(a, "/nonexistent/path/file.html")
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"404", data)

    def test_file_content_in_response(self):
        content = b"<p>Specific content here</p>"
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            f.write(content)
            path = f.name
        try:
            a, b = socket.socketpair()
            b.sendall(b"\r\n")
            serve_file(a, path)
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(content, data)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
