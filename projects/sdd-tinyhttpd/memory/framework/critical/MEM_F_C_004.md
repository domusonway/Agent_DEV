---
id: MEM_F_C_004
title: socket测试recv_all必须捕获ConnectionResetError和OSError，不只是timeout
tags:
  domain: general
  task_type: tdd_impl
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
任何使用socketpair()或真实socket的测试中，recv_all辅助函数必须捕获三类异常：
`socket.timeout`、`ConnectionResetError`、`OSError`

## 为什么是CRITICAL
只捕获timeout是最常见的测试helper错误。
当发送方在发送完毕后立即close时（HTTP响应的正常模式），
接收方可能收到ECONNRESET(104)而非优雅EOF，
导致测试ERROR而非正确判断实现是否正确。

## 反例→后果
```python
except socket.timeout:  # 只捕获timeout → 其他socket错误变成ERROR
    pass
```

## 正例
```python
except (socket.timeout, ConnectionResetError, OSError):
    pass
```

## 适用范围
所有涉及socket通信的测试helper函数（recv_all, read_response等）
