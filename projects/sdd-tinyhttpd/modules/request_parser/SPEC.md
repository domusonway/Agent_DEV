---
module: request_parser
id: M02
version: 0.1.0
status: locked
---

# 模块规格：request_parser

## 职责
从 socket conn 中读取并解析 HTTP 请求行和头部，返回 Request 对象。

## 接口定义

```python
from dataclasses import dataclass, field

@dataclass
class Request:
    method: str        # "GET" / "POST" / "HEAD"，大写
    url: str           # 原始 URL，含路径，不含 query string
    query_string: str  # query string（不含 ?），无则 ""
    headers: dict[str, str]  # 键全小写，如 "content-length"
    http_version: str  # "HTTP/1.0" / "HTTP/1.1"

def parse_request(conn: socket.socket) -> Request:
    """
    从 conn 读取 HTTP 请求行和全部头部（消费到空行 \r\n 为止）。
    调用返回后 conn 指向 body 起点（如有）。
    """

def get_line(conn: socket.socket) -> str:
    """逐字节读取一行，返回去掉 \r\n 的 str（内部使用）"""

def parse_content_length(conn: socket.socket) -> int:
    """
    读取头部直到找到 Content-Length，返回其值（int）。
    ⚠️ 注意：不消费空行，调用方读 body 前必须再调 drain_headers(conn)。
    """

def drain_headers(conn: socket.socket) -> None:
    """消费 conn 中剩余头部直到空行（\r\n），用于 body 读取前的对齐。"""
```

## 输出规格

| 返回 | 类型 | 说明 |
|------|------|------|
| Request | dataclass | method/url/query_string/headers/http_version 均为 str |
| content_length | int | `parse_content_length` 的返回值 |

## ⚠️ 本模块强制规则

- `get_line` 逐字节 `recv(1)`，必须检查 `b''`（连接关闭返回 `b''` 不抛异常）
- `recv(1)` 的 except：`except (socket.timeout, ConnectionResetError, OSError)`
- `parse_content_length` 返回后**空行仍在 socket 缓冲**，调用方必须先 `drain_headers`

## 行为约束

- method 转大写
- URL 按 `?` 分割：`?` 前为 url，`?` 后为 query_string
- 头部键转小写（`Content-Length` → `"content-length"`）
- 非法请求行（分割后字段数 ≠ 3）：raise ValueError

## 测试要点

- GET 请求：method="GET", url="/index.html", query_string=""
- GET 带 query：url="/cgi-bin/test.py", query_string="a=1&b=2"
- POST 请求：headers 含 "content-length"
- `drain_headers` 后 recv body 无多余前缀
- `get_line` 在 conn 关闭时返回 ""（不抛异常）

## 依赖

- 依赖模块：无
- 被依赖于：M03(router), M06(server)
- 第三方库：无（标准库 socket, dataclasses）
