"""
tests/validators/validate_response.py
校验 response 模块输出与fixture基准一致
先自测（应PASS），再交给implementer验证
"""
import pickle, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

MODULE_NAME = "response"
FIXTURES = Path(__file__).parent.parent / "fixtures"


def main():
    print(f"{'='*50}\n校验器: {MODULE_NAME}\n{'='*50}")

    ref = pickle.loads((FIXTURES / f"reference_{MODULE_NAME}_output.pkl").read_bytes())
    outputs = ref["outputs"]

    from modules.response.response import ok_headers, bad_request, not_found, cannot_execute, unimplemented

    fns = {
        "ok_headers": ok_headers,
        "bad_request": bad_request,
        "not_found": not_found,
        "cannot_execute": cannot_execute,
        "unimplemented": unimplemented,
    }

    errs = []
    for name, fn in fns.items():
        actual = fn()
        expected = outputs[name]
        if actual != expected:
            errs.append(f"{name}: 实际与基准不符\n  期望({len(expected)}B): {expected[:60]}\n  实际({len(actual)}B): {actual[:60]}")
        elif not isinstance(actual, bytes):
            errs.append(f"{name}: 返回类型应为bytes，实际{type(actual)}")

    if not errs:
        print(f"✅ 通过 — 全部{len(fns)}个响应函数输出与基准一致")
        sys.exit(0)
    else:
        print(f"❌ 失败 {len(errs)} 处:")
        for e in errs:
            print(f"  • {e}")
        print("→ 修改实现代码，不要修改fixture")
        sys.exit(1)


if __name__ == "__main__":
    main()
