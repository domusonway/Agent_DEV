---
id: MEM_F_C_005
title: recv返回空bytes(b'')表示连接关闭，必须检查
tags:
  domain: http_networking
  lang_stack: python
  task_type: tdd_impl, debugging
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
`conn.recv(n)` 在对端关闭连接时返回 `b''`（空bytes），不是None，不抛异常。
不检查会导致无限循环或处理空数据。

## 反例 → 后果
```python
while True:
    c = conn.recv(1)      # 连接关闭后永远返回b''
    buf += c              # 无限追加空bytes，CPU 100%
```

## 正例
```python
while True:
    c = conn.recv(1)
    if not c:             # b'' 是falsy
        break
    buf += c
```

## 与C的区别
C的recv()在连接关闭时返回0（字节数），tinyhttpd用`n > 0`判断。
Python对应：`if not data` 或 `if len(data) == 0`。
