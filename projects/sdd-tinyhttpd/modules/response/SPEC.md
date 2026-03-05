---
module: response
version: 0.1.0
status: locked
---

# 模块规格 - response

> 职责：向client socket发送标准HTTP错误响应和成功响应头

## 1. 职责
构造并发送HTTP响应bytes到socket，包含状态行、固定响应头、Body。不关闭socket。

## 2. 接口定义

```python
SERVER_STRING = b"Server: jdbhttpd/0.1.0\r\n"

def send_ok_headers(client: socket.socket, filename: str = "") -> None:
    """发送200 OK响应头（对应C版headers()）。"""

def send_bad_request(client: socket.socket) -> None:
    """发送400 Bad Request（POST无Content-Length时）。"""

def send_not_found(client: socket.socket) -> None:
    """发送404 Not Found。"""

def send_cannot_execute(client: socket.socket) -> None:
    """发送500 Internal Server Error（CGI执行失败）。"""

def send_unimplemented(client: socket.socket) -> None:
    """发送501 Method Not Implemented。"""
```

### 输出规格
| 函数 | 发送bytes | 说明 |
|------|---------|------|
| send_ok_headers | b"HTTP/1.0 200 OK\r\n" + SERVER_STRING + Content-Type + \r\n | 无Body |
| send_bad_request | b"HTTP/1.0 400 BAD REQUEST\r\n" + headers + HTML body | |
| send_not_found | b"HTTP/1.0 404 NOT FOUND\r\n" + headers + HTML body | |
| send_cannot_execute | b"HTTP/1.0 500 Internal Server Error\r\n" + headers + HTML body | |
| send_unimplemented | b"HTTP/1.0 501 Method Not Implemented\r\n" + headers + HTML body | |

## 3. 行为约束
- 所有函数使用socket.sendall()发送，确保完整发送
- 所有响应行以\r\n结尾
- 头部与body之间有空行\r\n
- Content-Type统一为text/html
- 不关闭socket（由调用方负责）
- filename参数当前不影响Content-Type（与原版一致）

## 4. 参考项目对应
| 功能 | 参考位置 |
|------|---------|
| headers() | httpd.c:296-310 |
| bad_request() | httpd.c:130-145 |
| not_found() | httpd.c:311-334 |
| cannot_execute() | httpd.c:158-171 |
| unimplemented() | httpd.c:385-406 |

## 5. 测试要点
- 每个函数发送的bytes以正确状态码开头
- 所有行结束符为\r\n
- 头部和body之间有空行
- socket接收到的bytes可被HTTP解析器识别

## 6. 依赖
- 依赖模块：无
- 被依赖于：static_handler, cgi_handler, router, server
- 第三方库：socket (标准库)
