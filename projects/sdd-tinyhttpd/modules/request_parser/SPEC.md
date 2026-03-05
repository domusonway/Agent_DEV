---
module: request_parser
version: 0.1.0
status: locked
---

# 模块规格 - request_parser

> 职责：从TCP socket读取HTTP请求并解析出结构化数据

## 1. 职责（单一职责）
逐字节从socket读取HTTP请求行，标准化行结束符，解析method/url/query_string。

## 2. 接口定义

```python
def get_line(sock: socket.socket) -> str:
    """从socket逐字节读取一行，标准化为以\n结尾的字符串（不含\r）。
    Returns: 行内容str。连接关闭返回空串""。最大读取4096字节防溢出。
    """

def parse_request_line(line: str) -> tuple[str, str, str]:
    """解析HTTP请求行。
    Args: line — get_line()返回的请求行，如 "GET /index.html HTTP/1.0\n"
    Returns: (method, url, protocol) 三元组，均为大写method，url保留原始大小写
    Raises: ValueError — 格式不合法（少于3个字段）
    """

def consume_headers(sock: socket.socket) -> dict[str, str]:
    """读取并丢弃/收集请求头，直到遇到空行（\n）为止。
    Returns: dict of header_name(lower) → value，用于CGI获取Content-Length
    """
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| sock | socket.socket | 已连接的客户端socket |
| line | str | get_line()的输出，以\n结尾 |

### 输出规格
| 函数 | 返回类型 | 说明 |
|------|---------|------|
| get_line | str | 以\n结尾，不含\r；空串表示连接断开 |
| parse_request_line | tuple[str,str,str] | (METHOD大写, url, protocol) |
| consume_headers | dict[str,str] | header名小写，值strip后的字符串 |

## 3. 行为约束
- \r\n → \n，单独\r → \n，单独\n → \n（与C版get_line一致）
- 超过4096字节截断（防DoS）
- parse_request_line: method转大写，url不变，protocol去除\n
- consume_headers: 遇到空行（只有\n）停止，返回已收集的headers dict

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| get_line | httpd.c:266-295 | 核心逐字节读取逻辑 |
| 请求行解析 | httpd.c:51-100 | accept_request前半段 |
| 消耗headers | httpd.c:102-105 | while strcmp("\n",buf) |

## 5. 测试要点
- get_line: \r\n → \n，单\r → \n，单\n → \n，空连接 → ""
- parse_request_line: GET/POST/DELETE，带query_string的url，缺字段抛ValueError
- consume_headers: 正常headers，Content-Length提取，空headers（直接空行）

## 6. 依赖
- 依赖模块：无
- 被依赖于：router, server
- 第三方库：socket (标准库)
