---
id: MEM_F_I_003
title: E2E测试能发现模块间隐式协议契约违反，单元测试无法覆盖
tags:
  domain: general
  lang_stack: python
  task_type: tdd_impl, debugging
  severity: IMPORTANT
created: 2026-03-03
expires: 2027-03-03
confidence: high
---

## 经验
网络协议重构中，各模块单元测试PASS不代表集成正确。
**必须在所有模块完成后，增加E2E集成测试**（启动真实服务器+真实socket客户端）。

## 根因（tinyhttpd验证）
单元测试用MockSocket喂入单一数据，不模拟完整HTTP报文格式。
模块间隐式协议契约（如：parse_content_length后谁负责drain空行）
无法通过单元测试发现，只有E2E测试才能暴露。

## 框架建议
SDD validator层应包含两类：
1. **模块级validator**：基于fixture比对，快速
2. **集成级validator**（`validate_<proj>_e2e.py`）：启动完整服务，覆盖模块间契约

集成validator应覆盖：
- 正常路径（GET静态、GET CGI、POST CGI）
- 错误路径（404、400、501、500）
- 安全边界（路径穿越）
- 协议格式（响应头CRLF、Server头）

## 实施要点
```python
# E2E测试模板关键点：
# 1. 用port=0让OS分配端口（避免冲突）
# 2. 服务器在daemon线程运行，stop_event控制退出
# 3. 客户端捕获ConnectionResetError（见MEM_F_I_001）
# 4. shutdown(SHUT_WR)触发服务器读到EOF
```
