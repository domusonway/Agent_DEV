---
module: request_parser
version: 0.1.0
status: locked
---

# 模块规格：request_parser

> 参考: httpd.c — get_line(), accept_request()的请求行解析部分

## 1. 职责
从 socket 读取 HTTP/1.0 请求行，解析出 method、url、query_string，并提供逐行读取工具。

## 2. 接口定义

```python
def get_line(conn: socket.socket) -> str
def parse_request_line(conn: socket.socket) -> dict
def drain_headers(conn: socket.socket) -> None
def parse_content_length(conn: socket.socket) -> int
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| conn | socket.socket | 已accept的客户端连接 |

### 输出规格
| 函数 | 返回类型 | 结构/说明 |
|------|---------|---------|
| get_line | str | 单行文本，含\n，不含\r，连接关闭返回"" |
| parse_request_line | dict | {"method": str, "url": str, "query_string": str} |
| drain_headers | None | 消耗剩余请求头直到空行，无返回值 |
| parse_content_length | int | 从头部解析Content-Length值，找不到返回-1 |

### parse_request_line 返回字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| method | str | 大写，如"GET"、"POST" |
| url | str | 不含query_string部分，如"/index.html" |
| query_string | str | ?之后的部分，无?则为"" |

## 3. 行为约束

### get_line 行为
- 逐字节recv，遇\r\n转为\n返回（丢弃\r）
- 遇裸\n直接返回
- 连接关闭(recv返回b'')返回""
- 最大行长度：1024字节（超出截断）

### parse_request_line 行为
- 读取第一行（get_line一次）
- 解析格式：`METHOD URL HTTP/version`
- method提取：第一个空格前的词，转大写
- url提取：method后跳过空格，到下一个空格
- query_string提取：url中?后的部分；同时将url截断到?之前
- GET请求有?: url截断，query_string=?后内容
- GET请求无?: query_string=""
- POST请求: query_string=""（不从URL提取）

### drain_headers 行为
- 循环调用get_line，直到读到"\n"（空行，即\r\n规范化后的\n）
- 用于丢弃不需要的请求头

### parse_content_length 行为
- 循环读取头部行
- 找到以"Content-Length:"开头的行（大小写不敏感）
- 返回其值（int）
- 读到空行（"\n"）时停止并返回-1（未找到）

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| get_line | httpd.c: get_line() | Python简化版，不需要size参数 |
| parse_request_line | httpd.c: accept_request() 前半部分 | 提取为独立函数 |
| drain_headers | httpd.c: serve_file()内的drain循环 | 多处使用，提取为工具 |
| parse_content_length | httpd.c: execute_cgi()内的头部解析 | 提取为独立函数 |

## 5. 测试要点
- 正常: GET /index.html HTTP/1.0 → {method:"GET", url:"/index.html", query_string:""}
- 正常: GET /cgi?name=foo HTTP/1.0 → {method:"GET", url:"/cgi", query_string:"name=foo"}
- 正常: POST /submit HTTP/1.0 → {method:"POST", url:"/submit", query_string:""}
- get_line: \r\n → "\n"（裸\r被去掉）
- parse_content_length: "Content-Length: 42\r\n" → 42
- parse_content_length: 无该头 → -1
- 校验基准: tests/fixtures/reference_request_parser_output.pkl（使用mock socket）

## 6. 依赖
- 依赖模块: 无
- 被依赖于: router, server(accept_request)
- 第三方库: socket（标准库）
