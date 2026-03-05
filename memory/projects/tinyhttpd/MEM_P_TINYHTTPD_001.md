---
id: MEM_P_TINYHTTPD_001
title: CGI错误处理：先验证可执行性，再发状态行
tags:
  domain: http_networking
  lang_stack: python
  task_type: tdd_impl, debugging
  severity: IMPORTANT
created: 2026-03-03
expires: never
confidence: high
---

## 经验
C版tinyhttpd的execute_cgi()在fork()之前就发出"HTTP/1.0 200 OK\r\n"。
fork失败时再调用cannot_execute()发500，导致客户端收到混乱头部（200+500）。

Python版翻译时如果照搬此逻辑，会产生相同问题：
先发200，Popen失败再发500，实际响应是两段头部拼接。

## 反例 → 后果
```python
conn.sendall(b"HTTP/1.0 200 OK\r\n")   # 先发
try:
    proc = Popen(...)
except FileNotFoundError:
    conn.sendall(cannot_execute())       # 后发，客户端收到混乱头部
```

## 正例（Python改进版）
```python
# 先验证脚本可执行性
if not os.path.isfile(path) or not os.access(path, os.X_OK):
    conn.sendall(cannot_execute())
    return
# 验证通过后才发200
conn.sendall(b"HTTP/1.0 200 OK\r\n")
proc = Popen(...)
```

## 推广价值
C→Python重构时，C版因fork成本低而将错误检查推迟到fork后的模式，
Python翻译时应提前到subprocess.Popen之前做预检，避免响应流污染。

## 对应修改
- modules/cgi_handler/cgi_handler.py: execute_cgi()
- CONTEXT.md §3: 已添加"CGI须预检可执行性"反模式
