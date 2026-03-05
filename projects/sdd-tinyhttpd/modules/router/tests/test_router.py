"""TDD测试 — router模块"""
import socket
import sys
import os
import stat
import tempfile
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.router import resolve_path, dispatch


def recv_all(sock, timeout=0.5):
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except (socket.timeout, ConnectionResetError, OSError):
        pass
    return data


class TestResolvePath(unittest.TestCase):
    def test_simple_url(self):
        path, qs, is_cgi = resolve_path("/index.html")
        self.assertEqual(path, "htdocs/index.html")
        self.assertEqual(qs, "")
        self.assertFalse(is_cgi)

    def test_root_url(self):
        path, qs, is_cgi = resolve_path("/")
        self.assertEqual(path, "htdocs/index.html")

    def test_url_with_query_string(self):
        path, qs, is_cgi = resolve_path("/cgi-bin/test.cgi?color=red")
        self.assertEqual(path, "htdocs/cgi-bin/test.cgi")
        self.assertEqual(qs, "color=red")
        self.assertTrue(is_cgi)

    def test_custom_htdocs_root(self):
        path, qs, is_cgi = resolve_path("/page.html", htdocs_root="/var/www")
        self.assertEqual(path, "/var/www/page.html")


class TestDispatch(unittest.TestCase):
    def setUp(self):
        # 创建临时htdocs目录
        self.tmpdir = tempfile.mkdtemp()
        self.htdocs = os.path.join(self.tmpdir, 'htdocs')
        os.makedirs(self.htdocs)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def make_static_file(self, name, content=b"<h1>Hello</h1>"):
        path = os.path.join(self.htdocs, name)
        with open(path, 'wb') as f:
            f.write(content)
        return path

    def make_cgi_script(self, name, content='echo "Content-Type: text/plain\r\n\r\nCGI OK"'):
        path = os.path.join(self.htdocs, name)
        with open(path, 'w') as f:
            f.write("#!/bin/sh\n" + content + "\n")
        os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
        return path

    def test_get_static_file_returns_200(self):
        self.make_static_file("test.html")
        a, b = socket.socketpair()
        b.sendall(b"\r\n")  # empty headers
        dispatch(a, 'GET', '/test.html', self.htdocs)
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"200 OK", data)
        self.assertIn(b"Hello", data)

    def test_get_nonexistent_returns_404(self):
        a, b = socket.socketpair()
        b.sendall(b"\r\n")
        dispatch(a, 'GET', '/missing.html', self.htdocs)
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"404", data)

    def test_delete_method_returns_501(self):
        a, b = socket.socketpair()
        b.sendall(b"\r\n")
        dispatch(a, 'DELETE', '/whatever', self.htdocs)
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"501", data)

    def test_get_cgi_with_query_string(self):
        self.make_cgi_script("test.cgi")
        a, b = socket.socketpair()
        b.sendall(b"\r\n")
        dispatch(a, 'GET', '/test.cgi?name=world', self.htdocs)
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"200", data)

    def test_executable_file_treated_as_cgi(self):
        self.make_cgi_script("exec_file.sh")
        a, b = socket.socketpair()
        b.sendall(b"\r\n")
        dispatch(a, 'GET', '/exec_file.sh', self.htdocs)
        a.close()
        data = recv_all(b)
        b.close()
        self.assertIn(b"200", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
