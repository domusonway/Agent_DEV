"""
modules/response/tests/test_response.py
RED阶段：测试先于实现，预期FAIL
使用unittest（标准库，无需安装）
"""
import pickle, sys, unittest
from pathlib import Path

FIXTURES = Path(__file__).parent.parent.parent.parent / "tests/fixtures"
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.response.response import ok_headers, bad_request, not_found, cannot_execute, unimplemented


def load_ref():
    data = pickle.loads((FIXTURES / "reference_response_output.pkl").read_bytes())
    return data["outputs"]


class TestResponseBytes(unittest.TestCase):
    def setUp(self):
        self.ref = load_ref()

    def test_ok_headers_returns_bytes(self):
        self.assertIsInstance(ok_headers(), bytes)

    def test_ok_headers_starts_with_200(self):
        self.assertTrue(ok_headers().startswith(b"HTTP/1.0 200 OK\r\n"))

    def test_ok_headers_matches_reference(self):
        self.assertEqual(ok_headers(), self.ref["ok_headers"])

    def test_bad_request_returns_bytes(self):
        self.assertIsInstance(bad_request(), bytes)

    def test_bad_request_starts_with_400(self):
        self.assertTrue(bad_request().startswith(b"HTTP/1.0 400 BAD REQUEST\r\n"))

    def test_bad_request_matches_reference(self):
        self.assertEqual(bad_request(), self.ref["bad_request"])

    def test_not_found_starts_with_404(self):
        self.assertTrue(not_found().startswith(b"HTTP/1.0 404 NOT FOUND\r\n"))

    def test_not_found_matches_reference(self):
        self.assertEqual(not_found(), self.ref["not_found"])

    def test_cannot_execute_starts_with_500(self):
        self.assertTrue(cannot_execute().startswith(b"HTTP/1.0 500"))

    def test_cannot_execute_matches_reference(self):
        self.assertEqual(cannot_execute(), self.ref["cannot_execute"])

    def test_unimplemented_starts_with_501(self):
        self.assertTrue(unimplemented().startswith(b"HTTP/1.0 501"))

    def test_unimplemented_matches_reference(self):
        self.assertEqual(unimplemented(), self.ref["unimplemented"])

    def test_no_bare_lf_in_any_response(self):
        for fn in [ok_headers, bad_request, not_found, cannot_execute, unimplemented]:
            result = fn()
            for i in range(1, len(result)):
                if result[i] == ord('\n'):
                    self.assertEqual(result[i-1], ord('\r'),
                        f"{fn.__name__}位置{i}有裸\\n")

    def test_ok_headers_ends_with_separator(self):
        self.assertTrue(ok_headers().endswith(b"\r\n\r\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
