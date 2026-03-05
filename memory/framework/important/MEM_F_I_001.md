---
id: MEM_F_I_001
title: socket集成测试中须捕获ConnectionResetError
tags:
  domain: http_networking
  lang_stack: python
  task_type: tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: 2027-03-03
confidence: high
---

## 经验
测试HTTP服务器时，服务器close连接后，客户端recv()可能收到ConnectionResetError
（Linux: ECONNRESET），而不是b""。

这是正常的TCP行为（服务器RST而非FIN），不是实现bug。
测试代码必须捕获此异常，否则测试误报FAIL。

## 反例 → 后果
```python
try:
    while True:
        chunk = client.recv(4096)
        if not chunk: break
        data += chunk
except socket.timeout:
    pass  # 只捕获timeout，ConnectionResetError会使测试ERROR
```

## 正例
```python
try:
    while True:
        chunk = client.recv(4096)
        if not chunk: break
        data += chunk
except (socket.timeout, ConnectionResetError):
    pass  # 两者都要捕获
```

## 根因
HTTP/1.0无Keep-Alive，服务器处理完立即close。
Linux TCP栈在close时可能发RST（尤其有未读数据时），
Python将ECONNRESET包装为ConnectionResetError（OSError子类）。
