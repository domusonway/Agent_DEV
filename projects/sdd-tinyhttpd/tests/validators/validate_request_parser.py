"""
tests/validators/validate_request_parser.py
校验 request_parser 模块输出与fixture基准一致

先自测（应PASS，因为fixture就是协议规范本身），再用于TDD验证。
"""
import io, pickle, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

MODULE_NAME = "request_parser"
FIXTURES = Path(__file__).parent.parent / "fixtures"


class MockSocket:
    """模拟socket：从bytes流逐字节recv"""
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    def recv(self, n: int, flags: int = 0) -> bytes:
        return self._buf.read(n)


def main():
    print(f"{'='*50}\n校验器: {MODULE_NAME}\n{'='*50}")

    ref = pickle.loads((FIXTURES / f"reference_{MODULE_NAME}_output.pkl").read_bytes())
    cases = ref["cases"]

    from modules.request_parser.request_parser import (
        get_line, parse_request_line, parse_content_length
    )

    errs = []

    # 校验 get_line
    for key in ["get_line_crlf", "get_line_lf"]:
        c = cases[key]
        sock = MockSocket(c["raw"])
        actual = get_line(sock)
        expected = c["expected_line"]
        if actual != expected:
            errs.append(f"{key}: 期望 {expected!r}，实际 {actual!r}")

    # 校验 parse_request_line
    for key in ["get_simple", "get_with_query", "post"]:
        c = cases[key]
        sock = MockSocket(c["raw"])
        actual = parse_request_line(sock)
        expected = c["expected"]
        for field in ["method", "url", "query_string"]:
            if actual.get(field) != expected[field]:
                errs.append(f"{key}.{field}: 期望 {expected[field]!r}，实际 {actual.get(field)!r}")

    # 校验 parse_content_length
    for key in ["content_length", "no_content_length"]:
        c = cases[key]
        sock = MockSocket(c["raw"])
        actual = parse_content_length(sock)
        expected = c["expected_cl"]
        if actual != expected:
            errs.append(f"{key}: 期望 {expected}，实际 {actual}")

    if not errs:
        print(f"✅ 通过 — 全部{sum(len(cases[k].get('expected',{}) or {'x':1}) for k in cases)}项检查通过")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        print("→ 修改实现代码，不要修改fixture")
        sys.exit(1)


if __name__ == "__main__":
    main()
