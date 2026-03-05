"""
static_handler.py — 静态文件服务
对应 httpd.c: serve_file(), cat()
"""
import socket
import os
from modules.request_parser import consume_headers
from modules.response import send_ok_headers, send_not_found

CHUNK_SIZE = 1024


def cat_file(client: socket.socket, path: str) -> None:
    """读取文件并分块发送到socket（对应C版cat()）"""
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            client.sendall(chunk)


def serve_file(client: socket.socket, path: str) -> None:
    """
    消耗剩余请求头，然后发送文件内容。
    文件不存在→404，存在→200 OK + 内容。
    """
    consume_headers(client)

    if not os.path.isfile(path):
        send_not_found(client)
        return

    send_ok_headers(client, path)
    cat_file(client, path)
