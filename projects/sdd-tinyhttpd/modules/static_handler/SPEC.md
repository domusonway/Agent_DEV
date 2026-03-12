---
module: static_handler
id: M04
version: 0.1.0
status: locked
---

# 模块规格：static_handler

## 职责
读取静态文件，构建完整 HTTP 响应（含 Content-Type），通过 conn 发送。

## 接口定义

```python
import socket
from ..request_parser import Request

def serve_file(conn: socket.socket, request: Request) -> None:
    """
    根据 request.url 读取 htdocs/ 下对应文件，发送完整 HTTP 响应。
    文件路径：htdocs + request.url（相对路径，依赖 cwd 含 htdocs/）
    url 为 "/" 时映射到 "htdocs/index.html"
    """

def guess_content_type(path: str) -> str:
    """根据文件扩展名返回 MIME 类型字符串"""
```

## 输出规格

| 情况 | 发送内容 |
|------|---------|
| 文件存在 | `response.build_response(200, body, content_type)` |
| 文件不存在 | `response.not_found()` |

所有发送通过 `conn.sendall(bytes)`，**返回 None**。

## ⚠️ 本模块强制规则

- `conn.sendall()` 参数必须是 **bytes**（来自 `response` 模块，已保证）
- 文件以 `"rb"` 打开（二进制，保持 bytes）
- url="/" 必须映射到 index.html，不得 404

## MIME 类型映射

| 扩展名 | MIME |
|--------|------|
| .html .htm | text/html |
| .css | text/css |
| .js | application/javascript |
| .png | image/png |
| .jpg .jpeg | image/jpeg |
| .gif | image/gif |
| 其他 | application/octet-stream |

## 测试要点

- 存在的 html 文件：响应含 200 + `text/html` + 文件内容
- 不存在文件：响应含 404
- url="/" 映射到 index.html
- 文件内容为 bytes 发送（不 decode）

## 依赖

- 依赖模块：M01(response), M02(Request)
- 被依赖于：M06(server)
- 标准库：os, pathlib
