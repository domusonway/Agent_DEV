---
id: MEM_F_I_002
title: C→Python重构：整数fd→socket对象，size参数→省略，全局→cwd
tags:
  domain: http_networking
  lang_stack: python
  task_type: spec_writing, tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: 2027-03-03
confidence: high
---

## 经验
C语言的三类设计在Python重构时有固定的转换模式：

### 1. 整数fd → socket对象
C: `void bad_request(int client)` 
Python: `def bad_request(conn: socket.socket) -> None`
不要用int fd，Python socket对象封装了fd并提供更安全的API。

### 2. buffer+size参数 → 省略（Python自动管理内存）
C: `int get_line(int sock, char *buf, int size)`
Python: `def get_line(conn: socket.socket) -> str`
Python字符串和bytes自动扩展，无需传入buffer和size。

### 3. 全局工作目录（htdocs相对路径）
C版用sprintf("htdocs%s", url)拼接相对路径，假设当前目录正确。
Python版继承此约定：必须在含htdocs/的目录下运行。
⚠️ 测试时要os.chdir到临时目录，否则路由找不到文件。

### 4. 错误处理提前（见MEM_P_TINYHTTPD_001）
C版fork()之后检查错误，Python版subprocess.Popen之前检查。
