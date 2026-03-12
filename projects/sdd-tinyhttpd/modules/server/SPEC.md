---
module: server
id: M06
version: 0.1.0
status: locked
---

# 模块规格：server

## 职责
TCP 主循环：绑定端口，accept 连接，每个连接开一个 daemon 线程执行 handle_client。

## 接口定义

```python
import socket

def handle_client(conn: socket.socket) -> None:
    """
    单个连接处理：parse → route → handler → close。
    所有异常在此捕获，确保 conn.close() 在 finally 中执行。
    """

def startup(port: int = 4000) -> None:
    """
    绑定端口，SO_REUSEADDR，无限循环 accept 连接，
    每个连接启动 Thread(target=handle_client, daemon=True)。
    """
```

## ⚠️ 本模块强制规则

- `conn.close()` 必须在 **finally** 块中（保证连接释放）
- `recv` 相关调用：`except (socket.timeout, ConnectionResetError, OSError)`
- `startup` 的 server socket：`SO_REUSEADDR` 必须设置（避免 TIME_WAIT 阻塞测试）
- Thread 必须设置 `daemon=True`（主线程退出时不阻塞）

## handle_client 流程

```python
def handle_client(conn: socket.socket) -> None:
    try:
        request = parse_request(conn)        # M02
        handler = route(request)             # M03
        handler(conn, request)               # M04 or M05
    except Exception as e:
        # 解析失败发 400
        try:
            conn.sendall(bad_request())
        except OSError:
            pass
    finally:
        conn.close()                         # 必须在 finally
```

## 测试要点

- `handle_client`：正常 GET 请求 → 调用 static_handler（可用 socketpair 测试）
- `handle_client`：异常请求 → 发送 400 响应，不抛出
- `startup`：`SO_REUSEADDR` 已设置
- 多并发连接不互相阻塞（daemon Thread）

## 依赖

- 依赖模块：M02(parse_request), M03(route), M01(bad_request)
- 被依赖于：无（顶层模块）
- 标准库：socket, threading
