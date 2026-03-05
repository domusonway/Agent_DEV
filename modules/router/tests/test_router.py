"""
modules/router/tests/test_router.py
路由逻辑测试（纯文件系统操作，无socket）
"""
import sys, os, unittest, tempfile, stat
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.router.router import resolve_path, should_use_cgi, route


class TestResolvePath(unittest.TestCase):
    def test_root_url(self):
        self.assertEqual(resolve_path("/"), "htdocs/index.html")

    def test_file_url(self):
        self.assertEqual(resolve_path("/about.html"), "htdocs/about.html")

    def test_subdir_trailing_slash(self):
        self.assertEqual(resolve_path("/sub/"), "htdocs/sub/index.html")

    def test_file_in_subdir(self):
        self.assertEqual(resolve_path("/sub/page.html"), "htdocs/sub/page.html")

    def test_no_double_slash(self):
        """确保路径不出现//"""
        path = resolve_path("/index.html")
        self.assertNotIn("//", path)


class TestShouldUseCgi(unittest.TestCase):
    def setUp(self):
        # 创建临时非可执行文件
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        self.tmp.write(b"hello")
        self.tmp.close()
        os.chmod(self.tmp.name, 0o644)  # 无执行权限

        # 创建临时可执行文件
        self.exe = tempfile.NamedTemporaryFile(delete=False, suffix=".cgi")
        self.exe.write(b"#!/bin/sh\necho hello")
        self.exe.close()
        os.chmod(self.exe.name, 0o755)  # 有执行权限

    def tearDown(self):
        os.unlink(self.tmp.name)
        os.unlink(self.exe.name)

    def test_post_is_cgi(self):
        self.assertTrue(should_use_cgi(self.tmp.name, "POST", ""))

    def test_get_with_query_is_cgi(self):
        self.assertTrue(should_use_cgi(self.tmp.name, "GET", "q=1"))

    def test_get_no_query_no_exec_is_static(self):
        self.assertFalse(should_use_cgi(self.tmp.name, "GET", ""))

    def test_executable_file_is_cgi(self):
        self.assertTrue(should_use_cgi(self.exe.name, "GET", ""))


class TestRoute(unittest.TestCase):
    def setUp(self):
        # 创建临时htdocs结构
        self.tmpdir = tempfile.mkdtemp()
        self.htdocs = os.path.join(self.tmpdir, "htdocs")
        os.makedirs(self.htdocs)
        # 写一个静态文件
        self.static = os.path.join(self.htdocs, "index.html")
        with open(self.static, "wb") as f:
            f.write(b"<html>hello</html>")
        os.chmod(self.static, 0o644)
        self._orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self._orig_dir)
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_existing_static_file(self):
        result = route("GET", "/index.html", "")
        self.assertTrue(result["exists"])
        self.assertFalse(result["is_cgi"])
        self.assertEqual(result["method"], "GET")

    def test_nonexistent_file(self):
        result = route("GET", "/nothere.html", "")
        self.assertFalse(result["exists"])

    def test_path_traversal_blocked(self):
        result = route("GET", "/../etc/passwd", "")
        self.assertFalse(result["exists"])

    def test_post_existing_file_is_cgi(self):
        result = route("POST", "/index.html", "")
        self.assertTrue(result["exists"])
        self.assertTrue(result["is_cgi"])

    def test_get_with_query_is_cgi(self):
        result = route("GET", "/index.html", "q=hello")
        self.assertTrue(result["exists"])
        self.assertTrue(result["is_cgi"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
