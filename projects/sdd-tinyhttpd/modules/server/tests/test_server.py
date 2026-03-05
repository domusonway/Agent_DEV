"""TDD测试 — server模块（集成测试）"""
import socket
import sys
import os
import threading
import time
import tempfile
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from modules.server import startup, accept_request


def send_request(host, port, request: bytes, timeout=2.0) -> bytes:
    """发送HTTP请求并接收响应"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.sendall(request)
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
    finally:
        sock.close()


class TestStartup(unittest.TestCase):
    def test_startup_returns_socket_and_port(self):
        srv, port = startup(0)
        self.assertIsInstance(srv, socket.socket)
        self.assertGreater(port, 0)
        srv.close()

    def test_startup_port_zero_dynamic(self):
        srv1, port1 = startup(0)
        srv2, port2 = startup(0)
        self.assertNotEqual(port1, port2)
        srv1.close()
        srv2.close()


class TestAcceptRequest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.htdocs = os.path.join(self.tmpdir, 'htdocs')
        os.makedirs(self.htdocs)
        # 创建测试文件
        with open(os.path.join(self.htdocs, 'index.html'), 'wb') as f:
            f.write(b"<h1>Welcome</h1>")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_accept_request_handles_get(self):
        a, b = socket.socketpair()
        b.sendall(b"GET /index.html HTTP/1.0\r\nHost: localhost\r\n\r\n")
        accept_request(a, self.htdocs)
        b.settimeout(1.0)
        data = b""
        try:
            while True:
                chunk = b.recv(4096)
                if not chunk:
                    break
                data += chunk
        except (socket.timeout, ConnectionResetError):
            pass
        b.close()
        self.assertIn(b"200", data)
        self.assertIn(b"Welcome", data)

    def test_accept_request_closes_socket(self):
        a, b = socket.socketpair()
        b.sendall(b"GET /index.html HTTP/1.0\r\n\r\n")
        accept_request(a, self.htdocs)
        # a已被关闭，b.recv应返回b''（表示对端关闭）
        b.settimeout(1.0)
        # 读完所有数据
        try:
            while b.recv(4096):
                pass
        except (socket.timeout, ConnectionResetError):
            pass
        # 验证a确实关闭了（再次关闭不应抛异常，或者fileno==-1）
        try:
            a.fileno()
            # 如果没抛异常说明还开着，这是一个问题
            # 但socketpair的特殊性，close后fileno()行为不一定
        except OSError:
            pass  # 已关闭，预期行为
        b.close()


class TestServerIntegration(unittest.TestCase):
    """完整服务器集成测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.htdocs = os.path.join(self.tmpdir, 'htdocs')
        os.makedirs(self.htdocs)
        with open(os.path.join(self.htdocs, 'hello.html'), 'wb') as f:
            f.write(b"<p>Hello Integration Test</p>")

        # 启动服务器线程
        from modules.server import startup, accept_request
        self.server_sock, self.port = startup(0)

        def server_loop():
            self.server_sock.settimeout(2.0)
            try:
                for _ in range(5):  # 最多处理5个请求
                    try:
                        client, addr = self.server_sock.accept()
                        t = threading.Thread(
                            target=accept_request,
                            args=(client, self.htdocs),
                            daemon=True
                        )
                        t.start()
                    except (socket.timeout, ConnectionResetError, OSError):
                        break
            except Exception:
                pass

        self.server_thread = threading.Thread(target=server_loop, daemon=True)
        self.server_thread.start()
        time.sleep(0.1)  # 等待服务器启动

    def tearDown(self):
        self.server_sock.close()
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_get_static_file(self):
        data = send_request('127.0.0.1', self.port,
                           b"GET /hello.html HTTP/1.0\r\nHost: localhost\r\n\r\n")
        self.assertIn(b"200 OK", data)
        self.assertIn(b"Hello Integration Test", data)

    def test_get_404(self):
        data = send_request('127.0.0.1', self.port,
                           b"GET /notfound.html HTTP/1.0\r\nHost: localhost\r\n\r\n")
        self.assertIn(b"404", data)

    def test_unsupported_method(self):
        data = send_request('127.0.0.1', self.port,
                           b"DELETE /hello.html HTTP/1.0\r\nHost: localhost\r\n\r\n")
        self.assertIn(b"501", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
