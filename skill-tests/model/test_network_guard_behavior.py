#!/usr/bin/env python3
"""
Layer 3: network-guard 行为测试
验证：模型在注入 network-guard HOOK 后，是否能正确审查代码并识别违规

测试方法：
  给模型有问题的 socket 代码片段，验证它能发现具体问题
  给模型正确的代码，验证它不会误报
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _api_client import read_skill, call_model, assert_model, AssertionError as ModelAssertionError

FRAMEWORK_ROOT = Path(__file__).parent.parent.parent.parent


def get_network_system() -> str:
    hook_content = read_skill(".claude/hooks/network-guard/HOOK.md")
    return f"""你是一个网络代码安全审查专家，严格按照以下 network-guard 规范审查代码：

{hook_content}

当我给你代码时，请：
1. 逐项检查清单
2. 指出所有违规点（引用具体行号或代码片段）
3. 给出修复建议
"""


def test_detect_bare_except():
    """能检测出裸 except（MEM_F_C_004 违规）"""
    system = get_network_system()
    code = """
def handle_client(conn):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            process(data)
        except:          # 问题在这里
            pass
    conn.close()
"""
    response = call_model(
        user_message=f"请检查这段代码：\n```python{code}```",
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型应该检测到裸 except（'except:'）违反了 MEM_F_C_004，并指出应改为 except (socket.timeout, ConnectionResetError, OSError)",
        context="代码中使用了裸 except: pass",
    )


def test_detect_missing_empty_bytes_check():
    """能检测出 recv 后没有 b'' 检查（MEM_F_C_005 违规）"""
    system = get_network_system()
    code = """
def read_all(conn):
    buf = b""
    while True:
        chunk = conn.recv(1024)
        buf += chunk          # 没有检查 b''
        if b"\\r\\n\\r\\n" in buf:
            break
    return buf
"""
    response = call_model(
        user_message=f"请检查这段代码：\n```python{code}```",
        system=system,
        max_tokens=600,
    )
    assert_model(
        response,
        criterion="模型应该检测到 recv() 后没有检查 b''（空 bytes），指出这会导致连接关闭后死循环",
        context="recv 后缺少 if not data: break 检查",
    )


def test_detect_send_instead_of_sendall():
    """能检测出用 .send() 代替 .sendall()"""
    system = get_network_system()
    code = """
def send_response(conn, response: bytes):
    conn.send(response)   # 应该用 sendall
    conn.close()
"""
    response = call_model(
        user_message=f"请检查这段代码：\n```python{code}```",
        system=system,
        max_tokens=500,
    )
    assert_model(
        response,
        criterion="模型应该指出 conn.send() 可能导致部分发送问题，建议改为 conn.sendall()",
        context="使用了 send 而非 sendall",
    )


def test_pass_clean_code():
    """正确代码不应该被误报"""
    system = get_network_system()
    code = """
import socket

def handle_client(conn: socket.socket) -> None:
    buf = b""
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            if b"\\r\\n\\r\\n" in buf:
                break
        except (socket.timeout, ConnectionResetError, OSError):
            break
    try:
        response = process_request(buf)
        conn.sendall(response)
    finally:
        conn.close()
"""
    response = call_model(
        user_message=f"请检查这段代码：\n```python{code}```",
        system=system,
        max_tokens=500,
    )
    assert_model(
        response,
        criterion="代码符合所有 network-guard 规范：有 b'' 检查、精确异常捕获、使用 sendall。模型不应该报告严重违规，应该给出通过或仅有轻微建议",
        context="这是符合规范的干净代码",
    )


def main():
    tests = [
        ("检测裸 except（MEM_F_C_004）", test_detect_bare_except),
        ("检测缺失 b'' 检查（MEM_F_C_005）", test_detect_missing_empty_bytes_check),
        ("检测 send 而非 sendall", test_detect_send_instead_of_sendall),
        ("正确代码不误报", test_pass_clean_code),
    ]

    print("Layer 3 · network-guard 行为测试")
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
