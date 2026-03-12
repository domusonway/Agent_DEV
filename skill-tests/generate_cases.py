#!/usr/bin/env python3
"""
Skill Test Case Generator
从 SKILL.md / HOOK.md 自动提取可测试约束，生成 generated/cases.json

用法：
  python3 skill-tests/generate_cases.py              # 生成全部 Skill 的用例
  python3 skill-tests/generate_cases.py --skill tdd-cycle   # 只重新生成指定 Skill
  python3 skill-tests/generate_cases.py --diff       # 仅处理有变更的 Skill（基于哈希）

生成结果写入 skill-tests/generated/cases.json，格式稳定，可提交到 git。
Runner (run_all.py --layer 2/3) 直接读取此文件，无需感知 Skill 内容。
"""

import json
import hashlib
import argparse
import urllib.request
import urllib.error
import time
from pathlib import Path
from datetime import datetime

FRAMEWORK_ROOT = Path(__file__).parent.parent
GENERATED_DIR = Path(__file__).parent / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

CASES_FILE = GENERATED_DIR / "cases.json"
HASH_FILE = GENERATED_DIR / ".skill_hashes.json"

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

# ── 注册所有需要生成测试用例的 Skill/Hook ────────────────────────────────────
SKILL_REGISTRY = [
    {
        "id": "tdd-cycle",
        "path": ".claude/skills/tdd-cycle/SKILL.md",
        "type": "skill",
        "layer2_trigger": "每次开始实现一个模块时",
        "description": "TDD 红绿重构循环",
    },
    {
        "id": "complexity-assess",
        "path": ".claude/skills/complexity-assess/SKILL.md",
        "type": "skill",
        "layer2_trigger": "收到开发任务后第一步",
        "description": "复杂度评估与模式选择",
    },
    {
        "id": "diagnose-bug",
        "path": ".claude/skills/diagnose-bug/SKILL.md",
        "type": "skill",
        "layer2_trigger": "RED 状态超过 2 次时",
        "description": "系统性 Bug 诊断",
    },
    {
        "id": "memory-update",
        "path": ".claude/skills/memory-update/SKILL.md",
        "type": "skill",
        "layer2_trigger": "所有模块 GREEN + VALIDATE 通过后，项目交付前",
        "description": "记忆沉淀与更新",
    },
    {
        "id": "validate-output",
        "path": ".claude/skills/validate-output/SKILL.md",
        "type": "skill",
        "layer2_trigger": "post-green hook 触发后，所有测试通过后",
        "description": "最终交付验收",
    },
    {
        "id": "network-guard",
        "path": ".claude/hooks/network-guard/HOOK.md",
        "type": "hook",
        "layer2_trigger": "写完任何含 recv/send/socket 的代码后，立即执行",
        "description": "网络代码安全检查",
    },
    {
        "id": "stuck-detector",
        "path": ".claude/hooks/stuck-detector/HOOK.md",
        "type": "hook",
        "layer2_trigger": "RED 状态连续超过 2 次",
        "description": "卡住状态检测与处理",
    },
    {
        "id": "post-green",
        "path": ".claude/hooks/post-green/HOOK.md",
        "type": "hook",
        "layer2_trigger": "所有测试变为 GREEN 后，立即执行",
        "description": "测试全绿后的后续动作",
    },
]

# ── EXTRACT PROMPT ────────────────────────────────────────────────────────────
EXTRACT_PROMPT = """你是一个测试用例设计专家。请阅读以下 {type_label} 文件，从中提取所有**可测试的行为约束**，并生成测试用例。

=== {skill_id} · {description} ===
{skill_content}

=== 提取要求 ===

请提取两类测试用例：

**Layer 2 - 触发测试**（1-2个）：
验证模型在什么场景下应该激活此 {type_label}。
已知触发时机：{trigger}

**Layer 3 - 行为测试**（3-6个）：
验证模型注入此 {type_label} 后，是否真正遵守其中的规则。
重点关注：
- 明确的禁止项（"禁止..."、"不允许..."、"必须..."）
- 强制流程步骤（"必须先...再..."）
- 边界条件（"超过N次..."、"如果...则..."）

对每个行为测试用例，设计一个"诱导场景"：故意让用户请求违反规则，验证模型是否抵制诱导。

=== 输出格式（严格 JSON，不要输出其他任何内容）===

{{
  "skill_id": "{skill_id}",
  "generated_at": "ISO时间戳",
  "layer2": [
    {{
      "name": "简短用例名（中文，≤20字）",
      "scenario": "触发此 {type_label} 的场景描述（1-2句话）",
      "criterion": "模型响应必须满足的条件（一句话，具体可判断）"
    }}
  ],
  "layer3": [
    {{
      "name": "简短用例名（中文，≤20字）",
      "group": "{skill_id}",
      "rule_source": "规则出处，引用 Skill 中的原文片段（≤30字）",
      "prompt": "诱导场景的用户输入（模拟用户试图违反规则）",
      "criterion": "模型响应必须满足的条件（一句话，具体可判断）",
      "system_hint": "需要注入的 Skill 内容关键段落（为空则注入全文）"
    }}
  ]
}}"""


# ── API ───────────────────────────────────────────────────────────────────────
def call_model(prompt: str, retries: int = 2) -> str:
    payload = {
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(retries + 1):
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                API_URL, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read())
                return result["content"][0]["text"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if attempt < retries and e.code in (429, 529):
                print(f"    Rate limit, waiting {5*(attempt+1)}s...")
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"API {e.code}: {body[:200]}") from e
        except Exception as e:
            if attempt < retries:
                time.sleep(3)
                continue
            raise


def extract_cases(skill: dict) -> dict:
    """从单个 Skill 文件提取测试用例"""
    skill_path = FRAMEWORK_ROOT / skill["path"]
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill 文件不存在: {skill_path}")

    content = skill_path.read_text(encoding="utf-8")
    type_label = "HOOK" if skill["type"] == "hook" else "SKILL"

    prompt = EXTRACT_PROMPT.format(
        skill_id=skill["id"],
        description=skill["description"],
        skill_content=content,
        trigger=skill["layer2_trigger"],
        type_label=type_label,
    )

    raw = call_model(prompt)

    # 解析 JSON（清理可能的 markdown fence）
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    cases = json.loads(clean)
    cases["generated_at"] = datetime.now().isoformat()
    cases["skill_path"] = skill["path"]
    cases["skill_hash"] = hashlib.md5(content.encode()).hexdigest()

    # 注入完整 Skill 内容作为默认 system（若 system_hint 为空）
    for c in cases.get("layer3", []):
        if not c.get("system_hint"):
            c["system_content"] = content
        else:
            c["system_content"] = f"{type_label}: {skill['id']}\n\n{content}\n\n关键规则：{c['system_hint']}"

    # Layer 2 统一用 routing system（由 runner 注入，此处不存 system）
    cases["layer2_trigger"] = skill["layer2_trigger"]

    return cases


# ── 哈希缓存：只重新生成有变更的 Skill ───────────────────────────────────────
def load_hashes() -> dict:
    if HASH_FILE.exists():
        return json.loads(HASH_FILE.read_text())
    return {}


def save_hashes(hashes: dict):
    HASH_FILE.write_text(json.dumps(hashes, indent=2))


def skill_hash(skill: dict) -> str:
    p = FRAMEWORK_ROOT / skill["path"]
    if not p.exists():
        return ""
    return hashlib.md5(p.read_text(encoding="utf-8").encode()).hexdigest()


# ── 主流程 ────────────────────────────────────────────────────────────────────
def load_existing() -> dict:
    if CASES_FILE.exists():
        return json.loads(CASES_FILE.read_text())
    return {"generated_at": "", "skills": {}}


def save(all_cases: dict):
    all_cases["generated_at"] = datetime.now().isoformat()
    CASES_FILE.write_text(json.dumps(all_cases, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Skill Test Case Generator")
    parser.add_argument("--skill", type=str, default=None, help="只生成指定 skill-id")
    parser.add_argument("--diff", action="store_true", help="只重新生成有变更的 Skill")
    parser.add_argument("--force", action="store_true", help="强制重新生成全部")
    args = parser.parse_args()

    print("=" * 56)
    print("  Skill Test Case Generator")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 56)

    all_cases = load_existing()
    if "skills" not in all_cases:
        all_cases["skills"] = {}

    hashes = load_hashes()

    targets = SKILL_REGISTRY
    if args.skill:
        targets = [s for s in SKILL_REGISTRY if s["id"] == args.skill]
        if not targets:
            print(f"❌ 未找到 skill: {args.skill}")
            print(f"   可用: {[s['id'] for s in SKILL_REGISTRY]}")
            return

    skipped = 0
    for skill in targets:
        current_hash = skill_hash(skill)
        cached_hash = hashes.get(skill["id"], "")

        # 决定是否跳过
        if not args.force and args.diff and current_hash == cached_hash and skill["id"] in all_cases["skills"]:
            print(f"  ─ {skill['id']:<24} (无变更，跳过)")
            skipped += 1
            continue

        print(f"\n  ⚙  {skill['id']} · {skill['description']}")
        print(f"     文件: {skill['path']}")

        try:
            cases = extract_cases(skill)
            l2_count = len(cases.get("layer2", []))
            l3_count = len(cases.get("layer3", []))

            all_cases["skills"][skill["id"]] = cases
            hashes[skill["id"]] = current_hash

            print(f"     ✅ Layer 2: {l2_count} 个触发用例")
            print(f"        Layer 3: {l3_count} 个行为用例")

            # 预览提取的用例名
            for c in cases.get("layer2", []):
                print(f"        L2 · {c['name']}")
            for c in cases.get("layer3", []):
                print(f"        L3 · {c['name']}  ← {c.get('rule_source','')}")

        except Exception as e:
            print(f"     ❌ 生成失败: {e}")
            # 保留旧用例，不覆盖
            continue

    save(all_cases)
    save_hashes(hashes)

    # 统计
    total_l2 = sum(len(v.get("layer2", [])) for v in all_cases["skills"].values())
    total_l3 = sum(len(v.get("layer3", [])) for v in all_cases["skills"].values())

    print(f"\n{'='*56}")
    print(f"  已保存: skill-tests/generated/cases.json")
    print(f"  覆盖 Skills: {len(all_cases['skills'])} 个")
    print(f"  Layer 2 用例: {total_l2} 个")
    print(f"  Layer 3 用例: {total_l3} 个")
    if skipped:
        print(f"  跳过（无变更）: {skipped} 个")
    print(f"{'='*56}")
    print()
    print("  → 执行测试: python3 skill-tests/run_all.py --layer 3")
    print("  → 更新单个: python3 skill-tests/generate_cases.py --skill tdd-cycle")
    print("  → 增量更新: python3 skill-tests/generate_cases.py --diff")


if __name__ == "__main__":
    main()
