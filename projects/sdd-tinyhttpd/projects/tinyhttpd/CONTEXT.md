# 项目上下文（CONTEXT.md）
# 项目: tinyhttpd — Python重构

> ⚠️ 所有 Agent 在读任何 SPEC.md 之前必须先完整阅读本文件

## 1. 领域知识前提

### 1.1 核心概念
| 概念 | 在本项目中的含义 | 常见误解 |
|------|----------------|---------|
| HTTP/1.0 | 无持久连接，每次请求后关闭socket | 误用HTTP/1.1 Keep-Alive |
| CRLF | HTTP协议行结束符必须是\r\n | 只用\n导致客户端解析失败 |
| CGI | 子进程执行脚本，stdin/stdout通信 | 误以为是RPC框架 |
| htdocs/ | 静态文件根目录，URL路径映射到此 | 路径遍历漏洞 |
| 可执行文件判断 | stat检查执行权限位决定是否走CGI | Python用os.access(path, os.X_OK) |

### 1.2 数据格式约定
```
HTTP请求（原始bytes）:
  请求行: "METHOD /path HTTP/1.x\r\n"
  头部:   "Header-Name: value\r\n" (多行)
  空行:   "\r\n"   ← 头部结束标志
  Body:   POST时存在，长度由Content-Length决定

Python socket通信: 统一用bytes
应用层字符串处理: str (decode latin-1保留所有字节)
```

### 1.3 核心数据流
```
client_socket
  → request_parser.get_line() → 请求行(method, url)
  → router决策(method, url, path, stat结果)
      ├── static_handler.serve_file(client, path)
      │     → response.headers() + cat()文件内容
      └── cgi_handler.execute_cgi(client, path, method, query_string)
            → subprocess → CGI脚本 → 输出转发给client
  → close(client_socket)
```

### 1.4 C→Python 关键映射
| C | Python | 注意 |
|---|--------|------|
| recv(sock,buf,1,0) | sock.recv(1) | 返回bytes，b''表示关闭 |
| send(sock,buf,len,0) | sock.sendall(data) | 保证全部发送 |
| fork()+execl() | subprocess.Popen | 更安全的替代 |
| S_IXUSR\|S_IXGRP\|S_IXOTH | os.access(path,os.X_OK) | |
| pipe()+dup2() | subprocess.PIPE | |

## 2. 运行环境约束

### 2.1 运行环境命令
```bash
python3   # Python 3.12，仅标准库
```

### 2.2 关键依赖
| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥3.8 | socket, os, subprocess, threading |
| 无第三方库 | - | 仅标准库 |

## 3. 反模式清单（⚠️ 禁止）

| 禁止做法 | 原因 | 正确替代 |
|---------|------|---------|
| str发送到socket | send()需bytes | encode()后发送 |
| recv后不检查空bytes | 连接关闭时返回b'' | if not data: break |
| URL直接拼接路径 | 路径遍历漏洞 | normpath+前缀检查 |
| \n代替\r\n | HTTP规范CRLF | 统一用b'\r\n' |

## 4. 参考项目关键设计决策

| 设计决策 | 原因 | 约束 |
|---------|------|------|
| 每请求一线程 | 简单并发 | Python用threading.Thread |
| HTTP/1.0 | 简化实现 | 处理完必须close socket |
| CGI fork+exec | Unix传统 | subprocess.Popen替代 |
| htdocs/为根 | 极简 | 保持一致 |

## 5. 模块间隐式契约

| 契约 | 方向 | 说明 |
|------|------|------|
| get_line返回字符串以\n结尾不含\r | parser→router | 调用方不需再strip \r |
| path已含htdocs/前缀 | router→handler | handler拿到完整文件系统路径 |
| serve_file负责消耗剩余请求头 | router→static | 调用前stream在第一个header行 |
| execute_cgi负责消耗请求头和body | router→cgi | 同上 |
| response函数只写bytes不关闭socket | handler→response | close由accept_request负责 |

## 6. 模块拆分

```
M01 request_parser  get_line, parse_request_line
M02 router          路由决策(method+path→handler)
M03 static_handler  serve_file, cat, 200 headers
M04 cgi_handler     execute_cgi (subprocess)
M05 response        错误响应(400/404/500/501)
M06 server          startup, accept_request, main
```

依赖拓扑: request_parser,response → router → static_handler,cgi_handler → server

## 变更历史
| 日期 | 修改内容 | 修改者 |
|------|---------|--------|
| 2026-03-03 | 初始创建 | planner |
