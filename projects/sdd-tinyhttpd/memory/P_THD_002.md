---
id: P_THD_002
title: POST body 读取偏移：parse_content_length 后必须 drain_headers
project: sdd-tinyhttpd
created: 2026-03-03
---

## 现象
POST 请求中，CGI 收到的 stdin body 前多了 `\r\n` 前缀，CGI 脚本解析失败。

## 根因
HTTP 请求结构：
```
POST /cgi-bin/test.py HTTP/1.0\r\n
Content-Length: 15\r\n      ← parse_content_length 读到这里 return
\r\n                         ← 空行仍在 socket 缓冲！
hello_post_body
```
`parse_content_length` 找到目标行即 return，不消费后续空行。
server 直接 `conn.recv(content_length)` 读到的前两字节是 `\r\n`。

## 修复
```python
content_length = parse_content_length(conn)
drain_headers(conn)  # 消费剩余头部直到空行
body = conn.recv(content_length)
```

## 单元测试为何未发现
MockSocket 喂入单一数据块，parse_content_length 消费完后 mock 就"空了"，
不存在"残留空行"的问题。E2E 测试才能发现真实 socket 的行为。

## 已升级为框架 Memory
→ framework/memory/domains/http/MEM_D_HTTP_005.md
→ 也验证了 MEM_F_I_003（E2E 测试发现隐式契约）
