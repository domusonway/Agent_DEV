---
id: MEM_P_TINYHTTPD_002
title: POST body读取偏移bug：parse_content_length后必须drain剩余headers
tags:
  domain: http_networking
  lang_stack: python
  task_type: debugging, diagnosis
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
`parse_content_length(conn)` 在找到 Content-Length 行后立即返回，
**不会消费后续的空行**（headers结束标志 `\r\n`）。

调用方（server.py）在读取POST body前，必须再调用 `drain_headers(conn)` 
消费掉剩余的headers（包括空行）。

## 根因（E2E调试发现）
HTTP请求结构：
```
POST /echo.cgi HTTP/1.0\r\n
Content-Length: 15\r\n      ← parse_content_length读到这里就return
\r\n                         ← 这个空行仍在socket缓冲区！
hello_post_body              ← body (15B)
```
若不drain，body读取得到 `\r\nhello_post_bo` (15B) 而非 `hello_post_body`。

## 反例 → 后果
```python
content_length = parse_content_length(conn)   # 返回15
# 直接读body：
body = conn.recv(content_length)               # 读到 b'\r\nhello_post_bo'！
```

## 正例
```python
content_length = parse_content_length(conn)
drain_headers(conn)          # ← 必须！消费空行及可能的其他headers
body = conn.recv(content_length)               # 读到 b'hello_post_body' ✓
```

## 发现方式
单元测试PASS（MockSocket逐字节，不含真实HTTP报文结构），
E2E测试T7 FAIL（body前多了`\r\n`前缀，实际读取偏移2字节）。

## 框架经验（可提升到framework）
E2E测试能发现模块间的隐式协议契约违反，
单元测试无法覆盖——因为MockSocket不模拟完整HTTP报文格式。
