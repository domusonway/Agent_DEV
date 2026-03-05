"""
cgi_handler.py — CGI脚本执行
对应 httpd.c: execute_cgi()
"""
import socket
import subprocess
import os
from modules.request_parser import consume_headers
from modules.response import send_bad_request, send_cannot_execute


def execute_cgi(client: socket.socket, path: str, method: str, query_string: str) -> None:
    """
    执行CGI脚本：
    - GET: 设置QUERY_STRING，消耗请求头
    - POST: 消耗请求头，读Content-Length，若无则400
    发送"HTTP/1.0 200 OK\r\n"后启动子进程，转发输出。
    """
    method = method.upper()
    content_length = -1

    if method == 'GET':
        consume_headers(client)
    else:  # POST
        headers = consume_headers(client)
        cl_str = headers.get('content-length', '')
        if not cl_str:
            send_bad_request(client)
            return
        try:
            content_length = int(cl_str)
        except ValueError:
            send_bad_request(client)
            return

    # 设置环境变量
    env = os.environ.copy()
    env['REQUEST_METHOD'] = method
    if method == 'GET':
        env['QUERY_STRING'] = query_string or ''
    else:
        env['CONTENT_LENGTH'] = str(content_length)

    # 发送200 OK（CGI自己负责后续头部）
    client.sendall(b"HTTP/1.0 200 OK\r\n")

    try:
        proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
    except (OSError, PermissionError):
        send_cannot_execute(client)
        return

    # POST: 从socket读body写入子进程stdin
    stdin_data = b""
    if method == 'POST' and content_length > 0:
        remaining = content_length
        while remaining > 0:
            chunk = client.recv(min(remaining, 1024))
            if not chunk:
                break
            stdin_data += chunk
            remaining -= len(chunk)

    stdout_data, _ = proc.communicate(input=stdin_data)
    client.sendall(stdout_data)
