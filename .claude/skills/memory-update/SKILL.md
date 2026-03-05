# SKILL: memory-update
# 触发：模块/项目完成后，或发现新的重要模式时
# 目的：将本次经验结构化写入 Memory，让下一个项目自动受益

## 判断是否值得写入

写入条件（满足任意一条）：
- 遇到了一个之前 Memory 没有记录的 Bug 类型
- 找到了某类问题的更好解决模式
- 发现了某个假设是错的（反面教材同样有价值）
- 某个技术决策（如 RLock vs Lock）有明确的理由

**不要写入**：
- 太具体到单个项目的细节（放项目记忆，不放框架记忆）
- 已有 Memory 记录覆盖的重复内容
- 还不确定是否普适的单次观察

## 写入格式

```markdown
---
id: MEM_F_C_XXX          # 框架级CRITICAL: MEM_F_C_
                          # 框架级IMPORTANT: MEM_F_I_
                          # 领域级: MEM_D_[领域]_
                          # 项目级: MEM_P_[项目]_
title: [一句话标题，说清楚是什么规则]
tags:
  domain: [networking / storage / parsing / general]
  lang_stack: python
  task_type: [tdd_impl / spec_writing / debugging / network_code]
  severity: CRITICAL / IMPORTANT / INFO
created: YYYY-MM-DD
validated_by: [验证来源，如"mini-redis对照实验"]
expires: never / YYYY-MM-DD
confidence: high / medium / low
---

## 经验
[核心规则，1–3句话，直接说结论]

## 原因
[为什么，机制解释]

## 反例 → 后果
[错误写法] → [导致什么问题]

## 正例
[正确写法，可含代码片段]

## 适用范围
[什么场景下这条规则适用]
```

## 写入后更新 INDEX

在 `memory/INDEX.md` 对应表格中添加新记录行：

```markdown
| MEM_F_C_XXX | [标题] | [适用场景] | framework/critical/MEM_F_C_XXX.md |
```

## 淘汰机制

- 每6个月审查一次 IMPORTANT 以下级别的记录
- 3个项目都未命中的记录降级或删除
- CRITICAL 级别需要明确反例才能删除
