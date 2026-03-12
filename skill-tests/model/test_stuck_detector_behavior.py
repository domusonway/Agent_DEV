#!/usr/bin/env python3
"""
Layer 3: stuck-detector + diagnose-bug 行为测试
验证：模型在触发 stuck-detector 后是否执行系统性诊断而非继续随机修改

这是最难验证的约束之一：
  错误行为 = 继续 "再试一次"
  正确行为 = 停下来、分类诊断、单点验证
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _api_client import read_skill, call_model, assert_model, AssertionError as ModelAssertionError

FRAMEWORK_ROOT = Path(__file__).parent.parent.parent.parent


def get_diagnose_system() -> str:
    stuck_content = read_skill(".claude/hooks/stuck-detector/HOOK.md")
    diagnose_content = read_skill(".claude/skills/diagnose-bug/SKILL.md")
    return f"""你是一个严格遵循 SDD 框架的 AI 编程助手。

当 stuck-detector 触发时（RED > 2 次），必须执行以下规范：

=== stuck-detector HOOK ===
{stuck_content}

=== diagnose-bug SKILL ===
{diagnose_content}

请严格按照这些规范处理卡住的调试场景。"""


def test_stop_random_changes():
    """
    核心约束：stuck 时必须停止随机修改
    模型不能在 RED>2 情况下继续推测性修改
    """
    system = get_diagnose_system()
    response = call_model(
        user_message="""
我的 test_parse_request 已经失败了 3 次。
错误是：AssertionError: assert result["method"] == "GET"

第1次改：把 split(" ") 改成 split(b" ")，还是失败
第2次改：加了 .decode("utf-8")，还是失败
第3次改：改了函数返回前的处理逻辑，还是失败

下一步我想试试用 re.split 替换 str.split，会有用吗？
        """.strip(),
        system=system,
        max_tokens=700,
    )
    assert_model(
        response,
        criterion="模型必须阻止继续随机猜测，明确说明需要停止修改代码，先完整读取错误信息（包含实际值），然后按分类诊断流程找根因",
        context="stuck-detector 场景：RED 超过 2 次，用户想继续随机尝试",
    )


def test_classify_type_error_correctly():
    """
    诊断分类：TypeError 应指向 dtype/bytes-str 问题
    """
    system = get_diagnose_system()
    response = call_model(
        user_message="""
我触发了 stuck-detector。完整错误信息：

  TypeError: a bytes-like object is required, not 'str'
    File "modules/server/server.py", line 38, in handle_request
      conn.sendall(response)

已经失败 3 次了，需要系统性诊断。
        """.strip(),
        system=system,
        max_tokens=700,
    )
    assert_model(
        response,
        criterion="模型应该将此错误分类为 bytes/str 类型错误，检查 response 的来源（应该是 bytes 但实际是 str），并追溯到 response 模块的返回类型，而不是建议继续随机修改",
        context="TypeError: bytes-like object required，这是典型的 dtype 错误",
    )


def test_require_print_repr_for_assertion_error():
    """
    诊断方法：AssertionError 时应要求打印 repr() 看实际值
    """
    system = get_diagnose_system()
    response = call_model(
        user_message="""
stuck-detector 触发。错误信息：

  AssertionError: assert result == b"HTTP/1.0 200 OK\\r\\n"
  
已尝试：
  1. 改了状态码格式，还是失败
  2. 改了换行符，还是失败
  3. 改了编码方式，还是失败
  
怎么诊断？
        """.strip(),
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型应该要求先用 print(repr(result)) 打印实际值，因为是 AssertionError，需要看实际值与期望值的精确差异（可能是 \\r\\n vs \\n，或其他不可见字符差异）",
        context="AssertionError 诊断方法：先看实际值",
    )


def test_single_point_change_principle():
    """
    核心原则：每次只改一处
    """
    system = get_diagnose_system()
    response = call_model(
        user_message="""
诊断后我有两个假设：
  假设A：是编码问题，应该用 latin-1 而不是 utf-8
  假设B：是换行符问题，应该用 \\r\\n 而不是 \\n

我想同时把两处都改了，一次性验证。
        """.strip(),
        system=system,
        max_tokens=500,
    )
    assert_model(
        response,
        criterion="模型必须阻止同时修改两处，说明每次只能改一处（单点验证原则），否则无法确定是哪个修复有效",
        context="诊断原则：每次只改一处，不能同时验证多个假设",
    )


def main():
    tests = [
        ("stuck 时必须停止随机修改", test_stop_random_changes),
        ("TypeError 正确分类为 dtype 问题", test_classify_type_error_correctly),
        ("AssertionError 要求 print(repr())", test_require_print_repr_for_assertion_error),
        ("坚持单点修改原则", test_single_point_change_principle),
    ]

    print("Layer 3 · stuck-detector 行为测试")
    print(f"{'─'*50}")
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except ModelAssertionError as e:
            print(f"  ❌ {name}")
            for line in str(e).strip().splitlines()[:3]:
                print(f"      {line}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {name} [ERROR: {e}]")
            failed += 1

    print(f"{'─'*50}")
    print(f"  {len(tests) - failed}/{len(tests)} 通过")
    sys.exit(failed)


if __name__ == "__main__":
    main()
