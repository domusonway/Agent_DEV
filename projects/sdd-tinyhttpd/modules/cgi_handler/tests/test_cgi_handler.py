"""TDD测试 — cgi_handler模块"""
import socket
import sys
import os
import stat
import tempfile
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.cgi_handler import execute_cgi


def recv_all(sock, timeout=1.0):
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


def make_cgi_script(content: str) -> str:
    """创建可执行的CGI脚本，返回路径"""
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.sh', delete=False,
        dir='/tmp'
    )
    f.write("#!/bin/sh\n")
    f.write(content)
    f.close()
    os.chmod(f.name, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
    return f.name


class TestExecuteCgiGet(unittest.TestCase):
    def test_get_cgi_returns_200_and_output(self):
        script = make_cgi_script('echo "Content-Type: text/plain\r\n\r\nHello CGI"\n')
        try:
            a, b = socket.socketpair()
            # 写入GET请求头（被consume_headers消耗）
            b.sendall(b"Host: localhost\r\n\r\n")
            execute_cgi(a, script, 'GET', 'name=world')
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(b"HTTP/1.0 200 OK", data)
            self.assertIn(b"Hello CGI", data)
        finally:
            os.unlink(script)

    def test_get_sets_query_string_env(self):
        # CGI脚本输出QUERY_STRING环境变量
        script = make_cgi_script('echo "QS=$QUERY_STRING"\n')
        try:
            a, b = socket.socketpair()
            b.sendall(b"\r\n")
            execute_cgi(a, script, 'GET', 'color=red&size=large')
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(b"color=red", data)
        finally:
            os.unlink(script)


class TestExecuteCgiPost(unittest.TestCase):
    def test_post_cgi_reads_body(self):
        # CGI读取stdin并输出
        script = make_cgi_script('read body; echo "BODY=$body"\n')
        try:
            a, b = socket.socketpair()
            body = b"name=test"
            headers = f"Content-Length: {len(body)}\r\n\r\n".encode()
            b.sendall(headers + body)
            execute_cgi(a, script, 'POST', '')
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(b"HTTP/1.0 200 OK", data)
        finally:
            os.unlink(script)

    def test_post_without_content_length_returns_400(self):
        script = make_cgi_script('echo "ok"\n')
        try:
            a, b = socket.socketpair()
            # 没有Content-Length头
            b.sendall(b"Host: localhost\r\n\r\n")
            execute_cgi(a, script, 'POST', '')
            a.close()
            data = recv_all(b)
            b.close()
            self.assertIn(b"400", data)
        finally:
            os.unlink(script)


class TestExecuteCgiErrors(unittest.TestCase):
    def test_nonexistent_script_returns_500(self):
        a, b = socket.socketpair()
        b.sendall(b"\r\n")
        execute_cgi(a, '/nonexistent/script.cgi', 'GET', '')
        a.close()
        data = recv_all(b)
        b.close()
        # 可能返回200(已发)+500错误，或直接500，检查500
        self.assertIn(b"500", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
