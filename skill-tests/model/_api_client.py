"""
共享 API 客户端 + 断言工具
供 Layer 2 和 Layer 3 测试使用

设计原则：
  - 所有模型调用带 system prompt（注入 Skill 内容）
  - 提供结构化 judge：不做字符串匹配，让模型判断语义是否满足
  - 每次调用有超时和重试
"""
import json
import time
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# 框架根目录（相对于本文件）
FRAMEWORK_ROOT = Path(__file__).parent.parent.parent.parent

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def read_skill(relative_path: str) -> str:
    """读取 SKILL.md 或 HOOK.md 内容"""
    path = FRAMEWORK_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Skill 文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def call_model(
    user_message: str,
    system: str = "",
    max_tokens: int = 1000,
    retries: int = 2,
) -> str:
    """调用 Claude API，返回文本响应"""
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_message}],
    }
    if system:
        payload["system"] = system

    for attempt in range(retries + 1):
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                API_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                return result["content"][0]["text"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if attempt < retries and e.code in (429, 529):
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"API Error {e.code}: {body}") from e
        except Exception as e:
            if attempt < retries:
                time.sleep(3)
                continue
            raise


def judge(
    response: str,
    criterion: str,
    context: str = "",
) -> tuple[bool, str]:
    """
    语义判断：让模型判断 response 是否满足 criterion。
    返回 (passed: bool, reason: str)

    这是 Layer 2/3 的核心：避免脆弱的字符串匹配，用语义理解做断言。
    """
    prompt = f"""你是一个严格的测试评估器。请判断以下【模型响应】是否满足【验证标准】。

【验证标准】
{criterion}

【背景信息】（可选）
{context}

【模型响应】
{response}

请仅输出 JSON，格式如下：
{{"passed": true或false, "reason": "一句话说明原因"}}

不要输出其他内容。"""

    result = call_model(prompt, max_tokens=200)
    try:
        # 清理可能的 markdown 代码块
        clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(clean)
        return bool(data["passed"]), str(data.get("reason", ""))
    except (json.JSONDecodeError, KeyError):
        # 降级：检查文本中有没有 true/false
        lower = result.lower()
        if '"passed": true' in lower or '"passed":true' in lower:
            return True, result
        return False, f"无法解析 judge 响应: {result[:100]}"


class AssertionError(Exception):
    """带 reason 的断言错误"""
    pass


def assert_model(response: str, criterion: str, context: str = "") -> None:
    """若不满足 criterion 则抛出 AssertionError"""
    passed, reason = judge(response, criterion, context)
    if not passed:
        raise AssertionError(
            f"断言失败\n  标准: {criterion}\n  原因: {reason}\n  响应片段: {response[:200]}"
        )
