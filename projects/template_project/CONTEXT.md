# 项目上下文（CONTEXT.md）
# 项目: tinyhttpd
# 参考: Tinyhttpd by J. David Blackstone (C语言，~433行)
# 目标: Python重构，沉淀C→Python重构经验和HTTP服务器开发经验

> ⚠️ 所有 Agent 在读任何 SPEC.md 之前必须先完整阅读本文件

---

## 1. 领域知识前提

### 1.1 HTTP/1.0 协议核心（tinyhttpd仅支持HTTP/1.0）

| 概念 | 在本项目中的含义 | 常见误解（Agent容易犯的错）|
|------|----------------|--------------------------|
| 请求行 | `METHOD URL HTTP/1.0\r\n` | 误用\n而非\r\n；URL可含?query |
| 请求头 | `Key: Value\r\n` 每行一个 | 头部结束是单独的`\r\n`空行 |
| CGI判断 | POST请求 OR URL含? OR 文件有执行权限 | 三个条件任一满足即触发CGI |
| get_line | 从socket读取一行，统一\r\n→\n | recv逐字节，\r\n要peek处理 |
| Content-Length | POST请求必须有，CGI读body依赖它 | 没有Content-Length→400 Bad Request |

### 1.2 响应格式约定（HTTP/1.0）
```
状态行:   HTTP/1.0 <code> <reason>\r\n
服务器头: Server: jdbhttpd/0.1.0\r\n
内容类型: Content-Type: text/html\r\n
空行:     \r\n
body:     <实际内容>
```
⚠️ tinyhttpd **不发送Content-Length响应头**（HTTP/1.0允许靠连接关闭判断body结束）

### 1.3 CGI执行机制
```
客户端 → server → fork() → 子进程execl(path)
                          环境变量: REQUEST_METHOD, QUERY_STRING/CONTENT_LENGTH
                          stdin←pipe←父进程转发POST body
                          stdout→pipe→父进程转发给客户端
父进程等待waitpid → 关闭连接
```

### 1.4 文件路由规则
```
URL → path = "htdocs" + URL
URL末尾是/ → 追加 index.html
stat(path)失败 → 404
path是目录 → 追加 /index.html
文件有执行权限(S_IXUSR|S_IXGRP|S_IXOTH) → CGI
否则 → 静态文件
```

### 1.5 并发模型
- C版本: pthread_create 每连接一线程
- Python版本: threading.Thread 每连接一线程（对应C设计）
- 不使用asyncio（偏离参考设计意图）

---

## 2. 运行环境约束

### 2.1 运行环境命令
```bash
python3        # 系统Python3（>=3.8），纯标准库
python3 -m pytest modules/ -v
python3 tests/run_all_validators.py
```

### 2.2 关键依赖
| 依赖 | 版本 | 原因 |
|------|------|------|
| socket | 标准库 | C的socket()对应 |
| threading | 标准库 | C的pthread对应 |
| subprocess | 标准库 | CGI执行（Python不fork，用subprocess） |
| os, stat | 标准库 | stat()文件属性检查 |
| pytest | 系统已有 | TDD测试 |

### 2.3 C→Python 关键转换约定
| C概念 | Python对应 | 注意 |
|-------|-----------|------|
| `int` socket fd | `socket.socket` 对象 | Python封装了fd |
| `recv(sock, buf, 1, 0)` | `conn.recv(1)` | 返回bytes |
| `send(client, buf, len, 0)` | `conn.sendall(data)` | sendall不截断 |
| `fork()+execl()` | `subprocess.Popen` | 更安全，不需要手动pipe |
| `pthread_create` | `threading.Thread` | daemon=True避免阻塞退出 |

---

## 3. 反模式清单（⚠️ 禁止实现方式）

| 禁止做法 | 原因 | 正确替代 |
|---------|------|---------|
| socket.recv()不检查返回空bytes | 连接关闭recv返回b''，不检查会死循环 | `if not data: break` |
| 用str而非bytes处理socket数据 | socket只认bytes，str会TypeError | 收发全程bytes，decode仅在解析层 |
| CGI用os.fork()+os.execl() | Python不推荐fork+多线程混用 | subprocess.Popen |
| 响应头用\n而非\r\n | HTTP协议强制\r\n，部分客户端拒绝\n | 所有响应行用`\r\n` |
| serve_file不关闭文件 | 文件描述符泄漏 | with open() as f |
| 线程中未捕获异常 | 异常静默消失，服务继续但行为异常 | try/except在accept_request顶层 |

---

## 4. 参考项目关键设计决策

| 设计决策 | 设计原因 | 对Python实现的约束 |
|---------|---------|-----------------|
| HTTP/1.0而非1.1 | 教学目的，简化实现 | 不实现Keep-Alive，每请求关闭连接 |
| 每连接一线程 | 简单并发模型 | 用threading.Thread，不用线程池 |
| get_line逐字节recv | socket无行边界，必须自己找\n | Python实现同样逐字节，或用makefile() |
| htdocs/作为根目录 | 隔离web文件 | 路径拼接必须防路径穿越(../) |
| CGI靠执行权限判断 | UNIX传统 | os.access(path, os.X_OK) |
| 服务器字符串固定 | 简单标识 | `Server: jdbhttpd/0.1.0\r\n` |

---

## 5. 模块间隐式契约

| 契约 | 方向 | 说明 |
|------|------|------|
| get_line返回行含\n不含\r | request_parser→router | 调用者假设已规范化，无需再处理\r |
| path已拼接htdocs前缀 | router→static_handler/cgi_handler | handler收到的是完整文件系统路径 |
| CGI handler收到的query_string不含? | router→cgi_handler | router已在?处截断，? 本身被去掉 |
| response函数直接send不缓冲 | response→所有handler | 每次send是独立数据包，顺序敏感 |
| conn在accept_request结束时关闭 | server→accept_request | handler不应关闭conn，由调用者管理（Python版调整：handler关闭） |

---

## 变更历史
| 日期 | 修改内容 | 修改者 |
|------|---------|--------|
| 2026-03-03 | 初始创建，基于httpd.c分析 | planner |
