---
id: P_THD_001
title: CGI 必须先验证可执行性再发状态行
project: sdd-tinyhttpd
created: 2026-03-03
---

## 现象
E2E 测试中，请求不存在的 CGI 路径时，客户端收到：
```
HTTP/1.0 200 OK
...（随后再收到）
HTTP/1.0 500 INTERNAL SERVER ERROR
```
头部混乱，客户端无法解析响应。

## 根因
直接移植 C 版逻辑：先 `send("HTTP/1.0 200 OK\r\n")`，fork 失败后再 send 500。
Python 版用 Popen，异常在 200 发出之后才触发。

## 修复
```python
# 先检查，后发状态行
if not os.path.isfile(path) or not os.access(path, os.X_OK):
    conn.sendall(response.cannot_execute())
    return
conn.sendall(b"HTTP/1.0 200 OK\r\n")  # 只有验证通过才发
```

## 已升级为框架 Memory
→ framework/memory/domains/http/MEM_D_HTTP_004.md
