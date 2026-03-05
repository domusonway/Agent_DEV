---
module: response
version: 0.1.0
status: locked
---

# 模块规格：response

> 参考: httpd.c — bad_request(), headers(), not_found(), cannot_execute(), unimplemented()

## 1. 职责
构造所有 HTTP/1.0 响应头和错误响应体，以 bytes 形式返回，供调用者 sendall()。

## 2. 接口定义

```python
def ok_headers(filename: str = "") -> bytes
def bad_request() -> bytes
def not_found() -> bytes
def cannot_execute() -> bytes
def unimplemented() -> bytes
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| filename | str | 仅ok_headers使用，当前版本忽略（Content-Type固定text/html）|

### 输出规格
| 函数 | 返回类型 | 内容 |
|------|---------|------|
| ok_headers | bytes | 200状态行+Server头+Content-Type头+空行 |
| bad_request | bytes | 400响应（含body HTML） |
| not_found | bytes | 404响应（含body HTML） |
| cannot_execute | bytes | 500响应（含body HTML） |
| unimplemented | bytes | 501响应（含body HTML） |

⚠️ 所有返回值必须是 `bytes`，不是 `str`

## 3. 行为约束

### 响应格式（严格遵循）
```
HTTP/1.0 <code> <reason>\r\n
Server: jdbhttpd/0.1.0\r\n          ← 除ok_headers外均包含
Content-Type: text/html\r\n
\r\n
<body HTML内容（error类函数）>
```

### ok_headers 格式
```
HTTP/1.0 200 OK\r\n
Server: jdbhttpd/0.1.0\r\n
Content-Type: text/html\r\n
\r\n
```
注：ok_headers不包含body，body由static_handler或cgi_handler提供

### 各响应状态码
| 函数 | 状态码 | Reason |
|------|--------|--------|
| ok_headers | 200 | OK |
| bad_request | 400 | BAD REQUEST |
| not_found | 404 | NOT FOUND |
| cannot_execute | 500 | Internal Server Error |
| unimplemented | 501 | Method Not Implemented |

### body内容（参考C版原文）
- bad_request body: `<P>Your browser sent a bad request, such as a POST without a Content-Length.\r\n`
- not_found body: 包含NOT FOUND标题和说明段落（参考C版not_found()）
- cannot_execute body: `<P>Error prohibited CGI execution.\r\n`
- unimplemented body: 包含Method Not Implemented标题和说明

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| ok_headers | httpd.c: headers() | filename参数当前版本忽略 |
| bad_request | httpd.c: bad_request() | |
| not_found | httpd.c: not_found() | |
| cannot_execute | httpd.c: cannot_execute() | |
| unimplemented | httpd.c: unimplemented() | |

## 5. 测试要点
- 正常: ok_headers()返回值以b"HTTP/1.0 200 OK\r\n"开头
- 正常: 每个函数返回bytes（不是str）
- 正常: 所有\n前面有\r（无裸\n）
- 正常: 头部结束有空行b"\r\n\r\n"（最后一个头之后）
- 边界: ok_headers("")和ok_headers("any.html")返回相同（当前版本）
- 校验基准: tests/fixtures/reference_response_output.pkl

## 6. 依赖
- 依赖模块: 无
- 被依赖于: static_handler, cgi_handler, server(accept_request)
- 第三方库: 无
