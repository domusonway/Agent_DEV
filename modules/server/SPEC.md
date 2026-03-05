---
module: server
version: 0.1.0
status: locked
---

# 模块规格：server

> 参考: httpd.c — startup(), main(), accept_request()

## 1. 职责
创建 TCP 监听 socket，循环 accept 连接，每连接启动线程调用 accept_request 处理完整请求。

## 2. 接口定义

```python
def startup(port: int = 0) -> tuple[socket.socket, int]
def accept_request(conn: socket.socket, addr: tuple) -> None
def run_server(port: int = 4000) -> None
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| port | int | 监听端口，0表示系统自动分配 |
| conn | socket.socket | accept()返回的客户端连接 |
| addr | tuple | (ip_str, port_int) 客户端地址 |

### 输出规格
| 函数 | 返回类型 | 说明 |
|------|---------|------|
| startup | tuple[socket.socket, int] | (server_socket, actual_port) |
| accept_request | None | 处理一个完整HTTP请求，副作用：发送响应，关闭conn |
| run_server | None | 阻塞运行，Ctrl+C退出 |

## 3. 行为约束

### startup
- socket(AF_INET, SOCK_STREAM)
- SO_REUSEADDR = 1（等同C版setsockopt）
- bind到('', port)
- port==0时getsockname()获取实际端口
- listen(5)
- 返回(server_sock, actual_port)

### accept_request 完整流程
```
1. parse_request_line(conn) → {method, url, query_string}
2. if method not in ("GET", "POST"): unimplemented(conn); return
3. if method == "POST": content_length = parse_content_length(conn)
   if content_length == -1: bad_request(conn); return
   body = recv_exact(conn, content_length)
   else: drain_headers(conn); body = b""
4. route(method, url, query_string) → {path, exists, is_cgi, ...}
5. if not exists: not_found(conn); return
6. if is_cgi: execute_cgi(conn, path, method, query_string, body)
   else: serve_file(conn, path)
7. conn.close()
```

### run_server
- 打印 "httpd running on port {port}"
- 循环accept，每连接 threading.Thread(target=accept_request, daemon=True)
- KeyboardInterrupt退出，关闭server_sock

### 线程安全
- 每个线程独占自己的conn，无共享状态
- htdocs/目录只读，无写操作，无需锁

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| startup | httpd.c: startup() | Python socket API |
| accept_request | httpd.c: accept_request() | 集成所有模块 |
| run_server | httpd.c: main() | pthread→threading |

## 5. 测试要点
- startup(0) 返回可用端口（非0）
- accept_request 集成测试：用socket对发（self-pipe）
- GET静态文件: 200+文件内容
- GET不存在: 404
- POST无Content-Length: 400
- 不支持方法(DELETE): 501
- 校验基准: 端到端测试（socket pair）

## 6. 依赖
- 依赖模块: request_parser, router, static_handler, cgi_handler, response
- 被依赖于: 无（顶层）
- 第三方库: socket, threading（标准库）
