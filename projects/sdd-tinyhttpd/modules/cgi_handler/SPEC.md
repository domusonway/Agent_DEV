---
module: cgi_handler
version: 0.1.0
status: locked
---

# 模块规格 - cgi_handler

> 职责：执行CGI脚本，将HTTP请求转发给子进程，将子进程输出转发给client

## 1. 职责
解析请求头获取Content-Length（POST），启动CGI子进程，双向转发数据。

## 2. 接口定义

```python
def execute_cgi(client: socket.socket, path: str, method: str, query_string: str) -> None:
    """
    执行CGI脚本并将输出发送给client。
    Args:
        client: 客户端socket
        path: CGI脚本路径（已含htdocs/前缀，已验证可执行）
        method: "GET" 或 "POST"（大写）
        query_string: GET时的查询字符串，POST时为""
    """
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| client | socket.socket | 客户端socket，stream在第一个header行 |
| path | str | CGI脚本完整路径 |
| method | str | "GET"或"POST"（大写） |
| query_string | str | URL?后的部分，GET时有效 |

## 3. 行为约束
- GET: 消耗并丢弃请求头，设置QUERY_STRING环境变量
- POST: 消耗请求头，提取Content-Length；若无Content-Length→send_bad_request，返回
- 发送"HTTP/1.0 200 OK\r\n"后启动子进程
- 环境变量: REQUEST_METHOD, QUERY_STRING(GET) 或 CONTENT_LENGTH(POST)
- POST: 从socket读取content_length字节写入子进程stdin
- 子进程stdout全部转发给client socket
- 子进程失败(启动失败)→send_cannot_execute

## 4. 参考项目对应
| 功能 | 参考位置 |
|------|---------|
| execute_cgi() | httpd.c:178-265 |

## 5. 测试要点
- GET CGI: 设置QUERY_STRING，子进程输出转发
- POST CGI: 读Content-Length，body写入stdin
- 无Content-Length的POST: 返回400
- CGI脚本不存在/不可执行: 返回500

## 6. 依赖
- 依赖模块：request_parser(consume_headers), response(send_bad_request, send_cannot_execute)
- 被依赖于：router
- 第三方库：subprocess, os (标准库)
