---
id: MEM_F_C_001
title: 校验器必须先用参考输出自测（应 PASS）
tags:
  domain: general
  lang_stack: python
  task_type: tdd_impl, validation
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
校验器创建后，**必须先用参考输出对自身运行一次**，确认应 PASS，再交给 Implementer。

## 反例 → 后果
未自测直接交给 Implementer → 校验器比对逻辑有 bug → 实现正确但误报失败 → 浪费多轮调试。

## 正例
```bash
python3 tests/validators/validate_<module>.py
# 预期: ✅ 通过
```
