---
id: MEM_D_HTTP_003
title: C→Python socket fd转换：Python用socket对象而非整数fd
tags:
  domain: http_networking
  lang_stack: python
  task_type: spec_writing, tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: never
confidence: high
---

## 经验
C版tinyhttpd的所有函数签名中第一个参数是`int client`（socket文件描述符）。
Python中对应的是`socket.socket`对象，所有SPEC接口定义必须使用socket对象，不用int fd。

## 接口转换表
| C函数签名 | Python函数签名 |
|-----------|---------------|
| `void bad_request(int client)` | `def bad_request(conn: socket.socket) -> None` |
| `void serve_file(int client, const char *filename)` | `def serve_file(conn: socket.socket, path: str) -> None` |
| `void execute_cgi(int client, ...)` | `def execute_cgi(conn: socket.socket, ...) -> None` |
| `int get_line(int sock, char *buf, int size)` | `def get_line(conn: socket.socket) -> str` |

## Python get_line 简化
C版get_line需要手动管理buffer大小参数，Python可以简化：
```python
def get_line(conn: socket.socket) -> str:
    """从socket读取一行，返回规范化字符串（含\n，不含\r）"""
    line = b""
    while True:
        c = conn.recv(1)
        if not c:
            break
        if c == b"\r":
            next_c = conn.recv(1)  # peek
            if next_c == b"\n":
                line += b"\n"
            else:
                line += b"\n"  # 丢弃\r，next_c未读（简化处理）
            break
        if c == b"\n":
            line += c
            break
        line += c
    return line.decode("utf-8", errors="replace")
```
