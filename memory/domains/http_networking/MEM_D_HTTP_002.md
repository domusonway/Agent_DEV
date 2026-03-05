---
id: MEM_D_HTTP_002
title: Python CGI执行用subprocess.Popen，不用os.fork()+os.execl()
tags:
  domain: http_networking
  lang_stack: python
  task_type: tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: never
confidence: high
---

## 经验
C版tinyhttpd用fork()+execl()执行CGI。Python中不推荐在多线程环境下使用os.fork()，
因为fork只复制调用线程，其他线程的锁状态会导致死锁。

## 正确方案：subprocess.Popen
```python
import subprocess, os

def execute_cgi(conn, path, method, query_string, content_length=0, body=b""):
    env = os.environ.copy()
    env["REQUEST_METHOD"] = method
    if method == "GET":
        env["QUERY_STRING"] = query_string or ""
    else:
        env["CONTENT_LENGTH"] = str(content_length)
    
    proc = subprocess.Popen(
        [path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    stdout, _ = proc.communicate(input=body)
    conn.sendall(stdout)
```

## 与C版本的等价性
| C | Python |
|---|--------|
| pipe(cgi_output) | stdout=subprocess.PIPE |
| pipe(cgi_input) | stdin=subprocess.PIPE |
| fork()+execl(path) | Popen([path]) |
| write(cgi_input[1], body) | proc.communicate(input=body) |
| read(cgi_output[0]) | stdout = proc.communicate()[0] |
| waitpid() | communicate()自动等待 |
