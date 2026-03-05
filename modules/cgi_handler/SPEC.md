---
module: cgi_handler
version: 0.1.0
status: locked
---

# 模块规格：cgi_handler

> 参考: httpd.c — execute_cgi()

## 1. 职责
执行 CGI 脚本，转发输入/输出，将 CGI 输出作为 HTTP 响应 body 发送给客户端。

## 2. 接口定义

```python
def execute_cgi(
    conn: socket.socket,
    path: str,
    method: str,
    query_string: str,
    body: bytes = b""
) -> None
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| conn | socket.socket | 已accept的客户端连接 |
| path | str | CGI脚本文件系统路径（可执行文件）|
| method | str | "GET"或"POST"（大写）|
| query_string | str | GET的query参数，POST时为""（已由router处理）|
| body | bytes | POST请求体，GET时为b"" |

### 输出规格
| 返回 | 类型 | 说明 |
|------|------|------|
| None | None | 副作用：向conn发送HTTP 200头+CGI输出 |

## 3. 行为约束

### 执行前发送200头
```python
conn.sendall(b"HTTP/1.0 200 OK\r\n")
```
（注：C版在fork前发，Python版在Popen前发，保持等价）

### 环境变量设置
| CGI环境变量 | 值 | 条件 |
|------------|-----|------|
| REQUEST_METHOD | method | 总是 |
| QUERY_STRING | query_string | method=="GET" |
| CONTENT_LENGTH | str(len(body)) | method=="POST" |

继承当前进程其他环境变量（os.environ.copy()）。

### CGI执行（subprocess.Popen）
```
stdin  = body（POST）或 b""（GET）
stdout = 捕获 → sendall给conn
stderr = 捕获但丢弃（不发给客户端）
```
使用 proc.communicate(input=body) 等待完成。

### 错误处理
- subprocess.Popen失败（如文件不可执行）→ 调用 cannot_execute(conn)
- CGI脚本返回非0退出码：仍发送其stdout（保持与C版一致）

### 不负责的工作
- 不负责读取请求头（由server在调用前通过parse_content_length完成）
- 不负责关闭conn（由server管理）

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| execute_cgi | httpd.c: execute_cgi() | fork+pipe改为subprocess.Popen |
| 环境变量 | httpd.c: execute_cgi() putenv部分 | |
| 200头 | httpd.c: execute_cgi() sprintf+send | |

## 5. 测试要点
- GET CGI: env有QUERY_STRING，无CONTENT_LENGTH，stdin为空
- POST CGI: env有CONTENT_LENGTH，stdin为body bytes
- 输出: 响应以b"HTTP/1.0 200 OK\r\n"开头，后跟CGI stdout
- 错误: 不可执行文件 → cannot_execute响应
- 校验: 用简单echo脚本（python3 -c "print('hello')"）验证输出转发
- 校验基准: tests/fixtures/reference_cgi_handler_output.pkl

## 6. 依赖
- 依赖模块: response（cannot_execute）
- 被依赖于: server(accept_request)
- 第三方库: subprocess, os（标准库）
