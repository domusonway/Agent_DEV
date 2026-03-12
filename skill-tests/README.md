# DEV SDD Framework — Skill Tests

## 三层验证架构

```
Layer 1: 文档结构测试   → 文档有没有必要内容？          快速，< 1s，无 API
Layer 2: 模型触发测试   → 场景 → 模型选对 Skill 了吗？  中速，~30s，调用 API
Layer 3: 模型行为测试   → 模型真的遵守约束了吗？         完整，~2min，调用 API
```

### 为什么需要三层？

**Layer 1（现有）的根本缺陷**：测试文档字符串存在性，不验证模型行为。

```python
# 原有测试
def test_has_stop_instruction():
    assert "停止" in content   # ← 文档有"停止"二字不等于模型会停下来
```

**Layer 2 验证触发逻辑**：给定场景，模型能否识别应该读取哪个 Skill？

**Layer 3 验证行为约束**：
- 模型是否拒绝跳过 RED 阶段？
- 模型是否拒绝修改断言？
- RED>2 次时模型是否停止随机修改？
- network-guard 能否检出具体违规？

---

## 用法

```bash
# Layer 1 仅文档结构（CI 默认，无 API 调用）
python3 skill-tests/run_all.py

# Layer 1 + 2（验证触发逻辑）
python3 skill-tests/run_all.py --layer 2

# 全部三层（完整验证，用于 Skill 修改后的回归测试）
python3 skill-tests/run_all.py --layer 3

# 只跑特定 Skill
python3 skill-tests/run_all.py --layer 3 --filter tdd
python3 skill-tests/run_all.py --layer 3 --filter network
python3 skill-tests/run_all.py --layer 3 --filter stuck
```

---

## 文件结构

```
skill-tests/
├── run_all.py                          ← 统一入口
├── README.md
├── cases/
│   ├── test_complexity_assess.py       ← Layer 1: 文档结构
│   ├── test_tdd_cycle.py
│   ├── test_diagnose_bug.py
│   ├── test_memory_update.py
│   ├── test_validate_output.py
│   ├── test_hook_network_guard.py
│   ├── test_hook_post_green.py
│   ├── test_hook_stuck_detector.py
│   └── model/
│       ├── _api_client.py              ← 共享：API 客户端 + judge()
│       ├── test_skill_trigger.py       ← Layer 2: 触发测试
│       ├── test_tdd_behavior.py        ← Layer 3: TDD 行为
│       ├── test_network_guard_behavior.py  ← Layer 3: network-guard 行为
│       └── test_stuck_detector_behavior.py ← Layer 3: stuck 行为
└── reports/                            ← 自动生成的测试报告
```

---

## judge() 工作原理

Layer 2/3 的核心是语义断言，而非字符串匹配：

```python
def judge(response: str, criterion: str) -> (bool, str):
    """让模型判断 response 是否满足 criterion"""
    # 避免脆弱的关键词匹配
    # 允许模型用不同措辞表达相同含义
```

**示例**：
- 标准：`"模型应该拒绝跳过 RED 阶段"`
- 响应A：`"不行，必须先写测试"` → PASS
- 响应B：`"好的，这是实现代码..."` → FAIL
- 响应C：`"根据 TDD 规范，在实现之前需要..."` → PASS

---

## 推荐工作流

| 场景 | 运行层级 |
|------|---------|
| 普通开发，快速确认文档结构 | Layer 1 |
| 修改了 SKILL.md 的激活条件 | Layer 1 + 2 |
| 修改了 SKILL.md 的规则内容 | Layer 1 + 2 + 3 |
| 发现 Skill 无效（模型不遵守）| Layer 3 → 改 Skill → 重测 |
| CI 流水线 | Layer 1（自动）+ Layer 3（手动触发）|
