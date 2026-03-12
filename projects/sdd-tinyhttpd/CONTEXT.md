# 项目上下文（CONTEXT.md）— sdd-tinyhttpd
# 参考：github.com/EZLippi/Tinyhttpd（C 实现）
# 目标：用 Python 重构 tinyhttpd，行为等价，代码可读

> ⚠️ 所有 Agent 在读任何 SPEC.md 之前必须先完整阅读本文件

---

## 1. 领域知识前提

### 1.1 HTTP/1.0 协议要点

| 概念 | 在本项目中的含义 | 常见误解 |
|------|----------------|---------|
| 请求行 | `METHOD URL HTTP/1.0\r\n` | 分隔符是 `\r\n` 不是 `\n` |
| 响应行 | `HTTP/1.0 STATUS TEXT\r\n` | 状态码文本必须精确匹配 |
| 头部结束 | 一个空行 `\r\n` | 头部和 body 之间有且仅有一个空行 |
| Content-Length | body 字节数（bytes），不是字符数 | str vs bytes 长度在多字节字符时不同 |

### 1.2 数据格式约定

```
socket 层：全程 bytes（recv/send/sendall 参数必须是 bytes）
应用层解析：bytes → decode('utf-8', errors='replace') → str
应用层处理：str（URL、Method、Header 值）
响应构建：str → encode('utf-8') → bytes → sendall
```

**单一转换点原则：bytes↔str 转换只在模块边界发生一次。**

### 1.3 核心数据流

```
TCP 连接
  │
  ▼
server.handle_client(conn)
  │
  ├─→ request_parser.parse_request(conn) → Request(method, url, headers)
  │
  ├─→ router.route(request) → handler_fn
  │
  ├─→ handler_fn(conn, request)
  │     ├─ static_handler.serve_file(conn, path)
  │     └─ cgi_handler.execute_cgi(conn, path, request)
  │
  └─→ conn.close()（在 finally）
```

---

## 2. C → Python 关键映射

| C 模式 | Python 替代 | 原因 |
|--------|------------|------|
| `int client`（fd） | `conn: socket.socket` 对象 | Python 封装了 fd |
| `char *buf, int size` | 省略 | Python 自动管理内存 |
| `fork() + execl()` | `subprocess.Popen` | 多线程环境 fork 危险 |
| `pthread_create` | `threading.Thread(daemon=True)` | |
| `sprintf("htdocs%s", url)` | `"htdocs" + url` | 相对路径依赖 cwd |
| `perror / exit(1)` | raise + 上层 except | Python 异常机制 |

---

## 3. 反模式清单（⚠️ 绝对禁止）

| 禁止做法 | 原因 | 正确替代 |
|---------|------|---------|
| `socket.sendall("HTTP/1.0 ...")` | send 需要 bytes | `.encode()` 后发送 |
| `recv()` 后不检查 `b''` | 连接关闭时死循环 CPU 100% | `if not data: break` |
| `except Exception` 捕获 socket 错误 | 掩盖正常关闭和真实错误 | `except (socket.timeout, ConnectionResetError, OSError)` |
| 先发 200 再检查 CGI 可执行性 | 头部混乱，客户端无法解析 | 先验证，再发状态行 |
| `parse_content_length` 后直接读 body | 空行仍在 socket 缓冲区 | 先 `drain_headers`，再读 body |
| `os.fork()` 执行 CGI | 多线程 + fork = 锁状态不一致 | `subprocess.Popen` |

---

## 4. 模块间隐式契约

| 契约 | 调用方向 | 说明 |
|------|---------|------|
| `parse_request` 消费请求行和所有请求头 | parser → server | server 调用 parse_request 后，conn 指针已过 `\r\n`（空行），可直接读 body |
| `parse_content_length` 不消费空行 | parser 内部 | 调用方（server）读 body 前**必须**再调 `drain_headers(conn)` |
| `serve_file` 负责发送完整响应（状态行+头+body） | static_handler → server | server 不再追加任何数据 |
| CGI 输出由 Popen stdout 直接转发 | cgi_handler → server | cgi_handler 负责整个响应，包括 `HTTP/1.0 200 OK\r\n` |

---

## 5. 模块拆分

```
M01 response          构建标准 HTTP 响应字节（状态行、头部、body 拼接）
M02 request_parser    解析 HTTP 请求行和头部，返回 Request 对象
M03 router            根据 method/url 分派到对应 handler
M04 static_handler    读取静态文件，调用 response 构建响应并发送
M05 cgi_handler       验证并执行 CGI 脚本，转发 stdout 到 conn
M06 server            主循环，accept 连接，多线程 handle_client

依赖拓扑（→ 被依赖于）：
  M01 → M04, M05
  M02 → M03, M06
  M03 → M06
  M04 → M06
  M05 → M06
  实现顺序: M01 → M02 → M03 → M04 → M05 → M06
```

---

## 变更历史

| 日期 | 修改内容 |
|------|---------|
| 2026-03-03 | 初始创建（M 模式） |
| 2026-03-05 | 框架 v3.0 重构，强制规则内联到各 SPEC.md |
