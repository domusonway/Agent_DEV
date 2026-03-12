---
module: response
id: M01
version: 0.1.0
status: locked
---

# 模块规格：response

## 职责
构建标准 HTTP/1.0 响应字节序列（状态行 + 头部 + body）。

## 接口定义

```python
def build_response(
    status_code: int,
    body: bytes = b"",
    content_type: str = "text/html",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    """
    返回完整 HTTP/1.0 响应 bytes。
    调用方直接 conn.sendall(build_response(...))。
    """

def not_found() -> bytes:
    """返回标准 404 响应 bytes"""

def bad_request() -> bytes:
    """返回标准 400 响应 bytes"""

def cannot_execute() -> bytes:
    """返回标准 500 响应 bytes（CGI 无法执行时）"""
```

## 输入/输出规格

| 参数 | 类型 | 约束 |
|------|------|------|
| status_code | int | 200 / 400 / 404 / 500 |
| body | bytes | 默认 b""，调用方负责编码 |
| content_type | str | MIME 字符串，默认 text/html |
| extra_headers | dict[str,str] \| None | 附加头部，如 Content-Length |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| response | **bytes** | 完整 HTTP 响应，全程 bytes，禁止混入 str |

## ⚠️ 本模块强制规则

- 所有响应行以 `\r\n` 结尾，**不是** `\n`
- 返回值必须是 `bytes`，调用方 `conn.sendall()` 不需要 encode
- `Content-Length` 值必须是 `len(body)`（bytes 长度，非 str 长度）

## 行为约束

```
HTTP/1.0 {status_code} {status_text}\r\n
Content-Type: {content_type}\r\n
Content-Length: {len(body)}\r\n
{extra_headers ...}\r\n
\r\n
{body}
```

状态码文本映射：
- 200 → "OK"
- 400 → "BAD REQUEST"  
- 404 → "NOT FOUND"
- 500 → "INTERNAL SERVER ERROR"

## 测试要点

- `build_response(200, b"hello")` 包含 `b"HTTP/1.0 200 OK\r\n"`
- 响应以 `b"\r\n\r\n"` 分隔头和 body
- `Content-Length` 值等于 `len(body)`
- `not_found()` 返回 bytes 且含 `b"404"`
- 空 body 时 `Content-Length: 0`

## 依赖

- 依赖模块：无
- 被依赖于：M04(static_handler), M05(cgi_handler)
- 第三方库：无（标准库）
