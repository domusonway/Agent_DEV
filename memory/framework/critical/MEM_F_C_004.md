---
id: MEM_F_C_004
title: socket recv 循环必须精确捕获 ConnectionResetError + OSError
tags:
  domain: networking, tcp_server
  lang_stack: python
  task_type: network_code, tdd_impl
  severity: CRITICAL
created: 2026-03-03
validated_by: mini-redis 2×2 对照实验（A/C命中预防，B/D未命中）
expires: never
confidence: high
---

## 经验

TCP 服务器 recv 循环**必须**使用精确异常捕获：

```python
# ✅ 正确
except (socket.timeout, ConnectionResetError, OSError):
    pass

# ❌ 错误（蒙混过关，掩盖真实语义）
except Exception:
    pass
```

## 原因

服务器发送最终响应后立刻 `close()` 连接，对端继续 `recv()` 时
收到 `ECONNRESET`（errno 104），Python 抛出 `ConnectionResetError`。
`except Exception` 虽能捕获，但：
- 掩盖正常关闭和真实错误的语义区别
- 高并发场景下会吞掉真实异常，产生静默 Bug

## 实验证据

mini-redis 2×2 对照实验（2026-03-03）：

| 组 | 加载 Memory | 首次代码 | 结果 |
|----|------------|---------|------|
| A  | ✅ | `except (socket.timeout, ConnectionResetError, OSError)` | ✅ 预防 |
| B  | ❌ | `except Exception` | ❌ 未命中 |
| C  | ✅ | `except (ConnectionResetError, OSError)` | ✅ 预防 |
| D  | ❌ | `except Exception` | ❌ 未命中 |

Memory 命中与分组完全吻合，是本实验最可信的单点结论。

## 在 CONTEXT.md §3 反模式中内联的标准文本

```markdown
- socket recv 循环只捕获 Exception → 必须改为
  `except (socket.timeout, ConnectionResetError, OSError)`（★MEM_F_C_004）
```

## 关联

- MEM_F_C_002：socket 发送必须 bytes（同属网络代码规范）
- hooks/network-guard：自动检查此规则的合规性
