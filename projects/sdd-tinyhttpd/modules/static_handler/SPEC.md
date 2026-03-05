---
module: static_handler
version: 0.1.0
status: locked
---

# 模块规格 - static_handler

> 职责：提供静态文件服务（消耗请求头、发送200响应头、传输文件内容）

## 1. 职责
消耗socket中剩余的HTTP请求头，然后读取文件并将内容发送给client。

## 2. 接口定义

```python
def serve_file(client: socket.socket, path: str, sock_reader=None) -> None:
    """
    消耗client socket中的剩余请求头，然后发送文件内容。
    Args:
        client: 客户端socket
        path: 文件系统绝对或相对路径（已含htdocs/前缀）
        sock_reader: 可选，用于测试时注入的读取函数（默认用request_parser.consume_headers）
    Raises: 文件不存在时调用response.send_not_found()，不抛异常
    """

def cat_file(client: socket.socket, path: str) -> None:
    """
    读取文件并分块发送到socket（对应C版cat()）。
    Args:
        client: 客户端socket
        path: 已验证存在的文件路径
    """
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| client | socket.socket | 客户端socket，stream在第一个header行 |
| path | str | 文件系统路径（含htdocs/前缀） |

## 3. 行为约束
- serve_file先消耗所有请求头（调用consume_headers）
- 文件不存在→调用send_not_found，不抛异常
- 文件存在→先send_ok_headers()，再cat_file()
- cat_file每次读取1024字节分块发送（与C版一致）
- cat_file发送完毕后不关闭socket

## 4. 参考项目对应
| 功能 | 参考位置 |
|------|---------|
| serve_file() | httpd.c:335-355 |
| cat() | httpd.c:146-157 |

## 5. 测试要点
- 文件存在：socket收到200 OK + 文件内容
- 文件不存在：socket收到404响应
- 大文件：分块发送，内容完整

## 6. 依赖
- 依赖模块：request_parser(consume_headers), response(send_ok_headers, send_not_found)
- 被依赖于：router
- 第三方库：os (标准库)
