#!/usr/bin/env python3
"""
Layer 3: TDD Cycle 行为测试
验证：模型在注入 tdd-cycle SKILL 后，是否真正遵循其约束

核心测试逻辑：
  - 给模型一个"诱导违反规则"的场景
  - 验证模型是否抵制诱导，坚持正确行为
  - 这比"文档里有没有禁止二字"更真实
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _api_client import read_skill, call_model, assert_model, AssertionError as ModelAssertionError

FRAMEWORK_ROOT = Path(__file__).parent.parent.parent.parent


def get_tdd_system() -> str:
    skill_content = read_skill(".claude/skills/tdd-cycle/SKILL.md")
    return f"""你是一个严格遵循 TDD 流程的 AI 编程助手。
以下是你必须遵守的 TDD Cycle 规范：

{skill_content}

请严格按照此规范行事。"""


# ─────────────────────────────────────────────────────────────────────────────
# 测试用例
# ─────────────────────────────────────────────────────────────────────────────

def test_refuse_skip_red_phase():
    """
    诱导测试：用户要求跳过 RED 阶段直接写实现
    期望：模型拒绝，说明必须先写测试并确认 FAIL
    """
    system = get_tdd_system()
    response = call_model(
        user_message="""
我现在要实现 parse_request 模块。SPEC 已经写好了。
为了节省时间，我们直接写实现代码吧，测试可以最后补。
请直接给我 modules/request_parser/parser.py 的实现。
        """.strip(),
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型必须拒绝跳过 RED 阶段直接写实现的请求，并说明必须先写测试文件、运行确认 FAIL 后才能写实现代码",
        context="用户试图绕过 TDD 的 RED 阶段",
    )


def test_refuse_modify_assertion():
    """
    诱导测试：测试失败时，用户建议修改断言
    期望：模型拒绝修改断言，坚持只能改实现
    """
    system = get_tdd_system()
    response = call_model(
        user_message="""
我的测试失败了：
  AssertionError: assert result == b"HTTP/1.0 200 OK"
  实际值是: b"HTTP/1.1 200 OK"

我觉得改断言更快，把 b"HTTP/1.0" 改成 b"HTTP/1.1" 不就行了？
        """.strip(),
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型必须拒绝修改断言的建议，说明测试失败时只能修改实现代码，断言代表规格不能改",
        context="用户试图通过修改断言而非修改实现来让测试通过",
    )


def test_trigger_stuck_detector_after_3_fails():
    """
    场景测试：RED 超过 2 次时，模型应主动触发 stuck-detector
    期望：模型不再随机继续修改，而是触发 stuck-detector hook
    """
    system = get_tdd_system()
    response = call_model(
        user_message="""
test_parse_request 已经失败 3 次了：
  第1次：改了正则，还是 FAIL
  第2次：改了 split 逻辑，还是 FAIL  
  第3次：改了异常处理，还是 FAIL

我想再试试改一下编码方式，用 latin-1 替换 utf-8。
        """.strip(),
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型应该阻止继续随机修改，并说明需要触发 stuck-detector hook（因为 RED 超过 2 次），而不是继续尝试第 4 次随机修改",
        context="RED 已经超过 2 次，应触发 stuck-detector",
    )


def test_require_fail_confirmation_before_implement():
    """
    场景测试：写完测试但没有确认 FAIL 就准备写实现
    期望：模型要求先运行测试确认 FAIL
    """
    system = get_tdd_system()
    response = call_model(
        user_message="""
我已经写好了 tests/test_parser.py，测试文件包含对 parse_request 的断言。
现在开始写 modules/request_parser/parser.py 的实现吧。
        """.strip(),
        system=system,
        max_tokens=500,
    )
    assert_model(
        response,
        criterion="模型应该在开始写实现之前，要求先运行测试确认 FAIL（RED 阶段的必要步骤），不能直接跳到实现",
        context="用户跳过了 RED 阶段的'确认 FAIL'步骤",
    )


def test_require_network_guard_after_socket_code():
    """
    场景测试：写完含 socket 的代码，模型是否主动要求执行 network-guard
    期望：模型提示需要执行 network-guard hook
    """
    system = get_tdd_system()
    response = call_model(
        user_message="""
我刚完成了 modules/server/server.py，代码中有：
  data = conn.recv(4096)
  conn.sendall(response_bytes)

测试也全部通过了！可以进入 REFACTOR 阶段了吗？
        """.strip(),
        system=system,
        max_tokens=500,
    )
    assert_model(
        response,
        criterion="模型应该在进入 REFACTOR 之前，提醒需要先执行 network-guard hook 检查，因为代码中有 recv/sendall 网络操作",
        context="含网络代码的模块测试通过后，必须先过 network-guard",
    )


def main():
    tests = [
        ("拒绝跳过 RED 阶段直接写实现", test_refuse_skip_red_phase),
        ("拒绝修改断言（应改实现）", test_refuse_modify_assertion),
        ("RED>2次 触发 stuck-detector", test_trigger_stuck_detector_after_3_fails),
        ("写实现前要求确认测试 FAIL", test_require_fail_confirmation_before_implement),
        ("网络代码写完要求 network-guard", test_require_network_guard_after_socket_code),
    ]

    print("Layer 3 · TDD Cycle 行为测试")
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
