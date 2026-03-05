---
module: server
version: 0.1.0
status: locked
---

# 模块规格 - server

> 职责：TCP监听、接受连接、多线程分发请求

## 1. 职责
创建TCP服务器socket，accept连接，每个连接启动一个线程处理。

## 2. 接口定义

```python
def startup(port: int = 0) -> tuple[socket.socket, int]:
    """
    创建TCP监听socket。
    Args: port — 监听端口，0表示系统自动分配
    Returns: (server_socket, actual_port)
    Raises: OSError — socket/bind/listen失败
    """

def accept_request(client_sock: socket.socket, htdocs_root: str = "htdocs") -> None:
    """
    处理单个HTTP请求（在线程中调用）。
    解析请求行→dispatch→close socket。
    捕获所有异常，确保socket被关闭。
    """

def run(port: int = 0, htdocs_root: str = "htdocs") -> None:
    """
    启动HTTP服务器主循环（阻塞）。
    每个连接启动daemon=True的线程调用accept_request。
    """
```

### 输出规格 - startup
| 返回 | 类型 | 说明 |
|------|------|------|
| server_socket | socket.socket | 已bind+listen的socket |
| actual_port | int | 实际监听端口（port=0时为系统分配） |

## 3. 行为约束
- startup: SO_REUSEADDR=True，listen backlog=5
- accept_request: 异常时确保close client_sock（try/finally）
- accept_request: 解析第一行失败（空行）→直接close，不发响应
- run: 线程daemon=True，KeyboardInterrupt优雅退出
- htdocs_root可配置，方便测试

## 4. 参考项目对应
| 功能 | 参考位置 |
|------|---------|
| startup() | httpd.c:356-384 |
| accept_request() | httpd.c:51-128 |
| main() pthread_create | httpd.c:407-432 |

## 5. 测试要点
- startup(0)返回可用端口
- accept_request完整处理GET请求后关闭socket
- 异常时socket仍被关闭

## 6. 依赖
- 依赖模块：request_parser, router
- 被依赖于：无（顶层）
- 第三方库：socket, threading (标准库)
