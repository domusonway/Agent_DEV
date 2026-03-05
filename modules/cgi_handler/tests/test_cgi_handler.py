"""
modules/cgi_handler/tests/test_cgi_handler.py
使用真实临时脚本测试CGI执行
"""
import sys, os, io, stat, unittest, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.cgi_handler.cgi_handler import execute_cgi


class MockSocket:
    def __init__(self):
        self._buf = io.BytesIO()

    def sendall(self, data: bytes):
        self._buf.write(data)

    @property
    def received(self) -> bytes:
        return self._buf.getvalue()


def make_script(content: str) -> str:
    """创建可执行Python CGI脚本"""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
    f.write("#!/usr/bin/env python3\n")
    f.write(content)
    f.close()
    os.chmod(f.name, 0o755)
    return f.name


class TestExecuteCgi(unittest.TestCase):
    def setUp(self):
        self.scripts = []

    def tearDown(self):
        for s in self.scripts:
            try:
                os.unlink(s)
            except Exception:
                pass

    def _script(self, content: str) -> str:
        path = make_script(content)
        self.scripts.append(path)
        return path

    def test_response_starts_with_200(self):
        path = self._script('import sys; sys.stdout.write("hello\\n")')
        sock = MockSocket()
        execute_cgi(sock, path, "GET", "", b"")
        self.assertTrue(sock.received.startswith(b"HTTP/1.0 200 OK\r\n"),
            f"响应应以200开头: {sock.received[:60]}")

    def test_get_cgi_output_forwarded(self):
        path = self._script('import sys; sys.stdout.write("cgi-output\\n")')
        sock = MockSocket()
        execute_cgi(sock, path, "GET", "q=test", b"")
        self.assertIn(b"cgi-output", sock.received)

    def test_get_query_string_env(self):
        path = self._script(
            'import os, sys\n'
            'qs = os.environ.get("QUERY_STRING", "NOT_SET")\n'
            'sys.stdout.write(f"QS={qs}\\n")\n'
        )
        sock = MockSocket()
        execute_cgi(sock, path, "GET", "name=foo", b"")
        self.assertIn(b"QS=name=foo", sock.received)

    def test_post_body_forwarded_to_stdin(self):
        path = self._script(
            'import sys\n'
            'body = sys.stdin.read()\n'
            'sys.stdout.write(f"BODY={body}")\n'
        )
        sock = MockSocket()
        execute_cgi(sock, path, "POST", "", b"hello=world")
        self.assertIn(b"BODY=hello=world", sock.received)

    def test_post_content_length_env(self):
        body = b"data=123"
        path = self._script(
            'import os, sys\n'
            'cl = os.environ.get("CONTENT_LENGTH", "NOT_SET")\n'
            'sys.stdout.write(f"CL={cl}\\n")\n'
        )
        sock = MockSocket()
        execute_cgi(sock, path, "POST", "", body)
        self.assertIn(f"CL={len(body)}".encode(), sock.received)

    def test_request_method_env(self):
        path = self._script(
            'import os, sys\n'
            'rm = os.environ.get("REQUEST_METHOD", "NOT_SET")\n'
            'sys.stdout.write(f"RM={rm}\\n")\n'
        )
        sock = MockSocket()
        execute_cgi(sock, path, "GET", "", b"")
        self.assertIn(b"RM=GET", sock.received)

    def test_invalid_script_returns_500(self):
        """不可执行或不存在的脚本应返回500"""
        sock = MockSocket()
        execute_cgi(sock, "/nonexistent/script.cgi", "GET", "", b"")
        self.assertTrue(sock.received.startswith(b"HTTP/1.0 500"),
            f"应返回500，实际: {sock.received[:60]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
