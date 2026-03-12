---
module: router
id: M03
version: 0.1.0
status: locked
---

# 模块规格：router

## 职责
根据 Request 的 method 和 url，决定使用哪个 handler，返回 handler 函数引用。

## 接口定义

```python
from typing import Callable
import socket
from .request_parser import Request

HandlerFn = Callable[[socket.socket, Request], None]

def route(request: Request) -> HandlerFn:
    """
    返回对应的 handler 函数。
    规则：
      - url 以 /cgi-bin/ 开头 → cgi_handler.execute_cgi
      - method == "POST"       → cgi_handler.execute_cgi
      - 其余                   → static_handler.serve_file
    """
```

## 输出规格

| 返回 | 类型 | 说明 |
|------|------|------|
| handler | Callable[[socket.socket, Request], None] | 函数引用，不调用 |

## ⚠️ 本模块强制规则

- router 只返回 handler，不调用它（调用由 server 负责）
- 不在此模块做任何 socket IO

## 测试要点

- `/cgi-bin/test.py` → 返回 `cgi_handler.execute_cgi`
- POST `/any` → 返回 `cgi_handler.execute_cgi`
- GET `/index.html` → 返回 `static_handler.serve_file`
- GET `/` → 返回 `static_handler.serve_file`

## 依赖

- 依赖模块：M02(request_parser 的 Request 类型)
- 被依赖于：M06(server)
