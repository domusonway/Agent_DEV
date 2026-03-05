---
id: MEM_F_C_002
title: SPEC 输出规格必须明确数值类型精度
tags:
  domain: general
  task_type: spec_writing
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
SPEC 输出表中，凡涉及数值，必须明确类型（int/str/bytes/dict结构）。
HTTP响应场景：必须明确是 `bytes` 还是 `str`，混用会在 socket.send() 处 TypeError。

## 反例 → 后果
SPEC 只写"返回响应内容" → 实现返回str → socket.sendall(str) → TypeError。

## 正例
```
| 返回 | 类型 | 说明 |
|------|------|------|
| response | bytes | HTTP响应，含头部和body，全程bytes |
```
