---
id: MEM_D_HTTP_001
title: HTTP响应行必须用\r\n，不能只用\n
tags:
  domain: http_networking
  lang_stack: python
  task_type: tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: never
confidence: high
---

## 经验
HTTP/1.0和HTTP/1.1协议规定，所有响应头行结束必须使用CRLF(`\r\n`)。
仅用`\n`在curl/浏览器可能正常（容错），但在严格客户端或测试中会失败。

## 正例
```python
STATUS_LINES = {
    200: b"HTTP/1.0 200 OK\r\n",
    400: b"HTTP/1.0 400 BAD REQUEST\r\n",
    404: b"HTTP/1.0 404 NOT FOUND\r\n",
    500: b"HTTP/1.0 500 Internal Server Error\r\n",
    501: b"HTTP/1.0 501 Method Not Implemented\r\n",
}
HEADER_SEP = b"\r\n"  # 头部结束空行
```

## 测试策略
校验器检查响应bytes中是否包含`b"\r\n"`而非`b"\n"`。
