"""
response.py — HTTP错误响应模块
对应 httpd.c: headers(), bad_request(), not_found(), cannot_execute(), unimplemented()
"""
import socket

SERVER_STRING = b"Server: jdbhttpd/0.1.0\r\n"


def _send(client: socket.socket, data: bytes) -> None:
    client.sendall(data)


def send_ok_headers(client: socket.socket, filename: str = "") -> None:
    """发送200 OK响应头（对应C版headers()）"""
    _send(client, b"HTTP/1.0 200 OK\r\n")
    _send(client, SERVER_STRING)
    _send(client, b"Content-Type: text/html\r\n")
    _send(client, b"\r\n")


def send_bad_request(client: socket.socket) -> None:
    """发送400 Bad Request"""
    _send(client, b"HTTP/1.0 400 BAD REQUEST\r\n")
    _send(client, b"Content-Type: text/html\r\n")
    _send(client, b"\r\n")
    _send(client, b"<P>Your browser sent a bad request, ")
    _send(client, b"such as a POST without a Content-Length.\r\n")


def send_not_found(client: socket.socket) -> None:
    """发送404 Not Found"""
    _send(client, b"HTTP/1.0 404 NOT FOUND\r\n")
    _send(client, SERVER_STRING)
    _send(client, b"Content-Type: text/html\r\n")
    _send(client, b"\r\n")
    _send(client, b"<HTML><TITLE>Not Found</TITLE>\r\n")
    _send(client, b"<BODY><P>The server could not fulfill\r\n")
    _send(client, b"your request because the resource specified\r\n")
    _send(client, b"is unavailable or nonexistent.\r\n")
    _send(client, b"</BODY></HTML>\r\n")


def send_cannot_execute(client: socket.socket) -> None:
    """发送500 Internal Server Error"""
    _send(client, b"HTTP/1.0 500 Internal Server Error\r\n")
    _send(client, b"Content-Type: text/html\r\n")
    _send(client, b"\r\n")
    _send(client, b"<P>Error prohibited CGI execution.\r\n")


def send_unimplemented(client: socket.socket) -> None:
    """发送501 Method Not Implemented"""
    _send(client, b"HTTP/1.0 501 Method Not Implemented\r\n")
    _send(client, SERVER_STRING)
    _send(client, b"Content-Type: text/html\r\n")
    _send(client, b"\r\n")
    _send(client, b"<HTML><HEAD><TITLE>Method Not Implemented\r\n")
    _send(client, b"</TITLE></HEAD>\r\n")
    _send(client, b"<BODY><P>HTTP request method not supported.\r\n")
    _send(client, b"</BODY></HTML>\r\n")
