---
module: cgi_handler
id: M05
version: 0.1.0
status: locked
---

# 模块规格：cgi_handler

## 职责
验证 CGI 脚本可执行性，设置环境变量，执行脚本，转发 stdout 到 conn。

## 接口定义

```python
import socket
from ..request_parser import Request

def execute_cgi(conn: socket.socket, request: Request) -> None:
    """
    1. 验证 htdocs/request.url 文件存在且可执行
    2. 不可执行 → sendall(response.cannot_execute()) 并 return
    3. 可执行 → sendall(b"HTTP/1.0 200 OK\r\n") 再执行
    4. 用 subprocess.Popen 执行，stdin 传 POST body（如有）
    5. stdout 直接 sendall 到 conn
    """
```

## ⚠️ 本模块强制规则

- **先验证可执行性，再发状态行**（禁止先发 200 再检查）
- 用 `subprocess.Popen`，**禁止** `os.fork()`（多线程环境）
- POST body：先 `parse_content_length(conn)`，再 `drain_headers(conn)`，再 `conn.recv(content_length)`
- sendall 参数必须是 **bytes**

## 环境变量设置

| 变量 | 值来源 |
|------|--------|
| REQUEST_METHOD | request.method |
| QUERY_STRING | request.query_string |
| CONTENT_LENGTH | str(content_length)（POST 时） |
| SERVER_NAME | "localhost" |

## 行为约束

```
if not os.path.isfile(path) or not os.access(path, os.X_OK):
    conn.sendall(response.cannot_execute())
    return

conn.sendall(b"HTTP/1.0 200 OK\r\n")
proc = subprocess.Popen(...)
stdout, _ = proc.communicate(input=body)
conn.sendall(stdout)
```

## 测试要点

- 不存在文件：发送 500 响应，不发 200
- 不可执行文件：发送 500，不执行
- GET 请求：QUERY_STRING 设置正确，stdin 为空
- POST 请求：body 正确传给 stdin，CONTENT_LENGTH 正确

## 依赖

- 依赖模块：M01(response), M02(request_parser)
- 被依赖于：M06(server)
- 标准库：os, subprocess
