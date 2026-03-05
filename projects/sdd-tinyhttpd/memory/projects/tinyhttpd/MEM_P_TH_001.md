---
id: MEM_P_TH_001
title: socketpair测试recv_all必须捕获ConnectionResetError和OSError
tags:
  domain: http_server
  task_type: tdd_impl
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
用socketpair测试HTTP响应时，send方close socket后，recv方可能收到ConnectionResetError(errno 104)而非优雅的EOF(b'')。

## 触发场景
- 测试send_unimplemented()等立即close后不再写的响应函数
- server发完501后close，测试端接着recv

## 反例→后果
只捕获`socket.timeout`的recv_all → 测试ERROR而非PASS，掩盖了实现正确的事实。

## 正例
```python
except (socket.timeout, ConnectionResetError, OSError):
    pass
```

## 是否沉淀到框架
是→framework/important/：socketpair测试的通用模式
