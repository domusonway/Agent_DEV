"""
modules/response/response.py
HTTP/1.0 响应构造模块

对应 httpd.c: headers(), bad_request(), not_found(), cannot_execute(), unimplemented()
全程返回 bytes，不含 str。
"""

_SERVER = b"Server: jdbhttpd/0.1.0\r\n"
_CT_HTML = b"Content-Type: text/html\r\n"
_SEP = b"\r\n"


def ok_headers(filename: str = "") -> bytes:
    """构造 HTTP/1.0 200 OK 响应头（不含body）。
    
    对应 httpd.c: headers()
    filename 参数保留接口兼容性，当前版本忽略（Content-Type固定text/html）。
    """
    return (
        b"HTTP/1.0 200 OK\r\n"
        + _SERVER
        + _CT_HTML
        + _SEP
    )


def bad_request() -> bytes:
    """构造 400 Bad Request 完整响应（含body）。
    
    对应 httpd.c: bad_request()
    触发条件：POST请求缺少Content-Length头。
    """
    return (
        b"HTTP/1.0 400 BAD REQUEST\r\n"
        + _CT_HTML
        + _SEP
        + b"<P>Your browser sent a bad request, "
        b"such as a POST without a Content-Length.\r\n"
    )


def not_found() -> bytes:
    """构造 404 Not Found 完整响应（含body）。
    
    对应 httpd.c: not_found()
    """
    return (
        b"HTTP/1.0 404 NOT FOUND\r\n"
        + _SERVER
        + _CT_HTML
        + _SEP
        + b"<HTML><TITLE>Not Found</TITLE>\r\n"
        b"<BODY><P>The server could not fulfill\r\n"
        b"your request because the resource specified\r\n"
        b"is not found on the server.\r\n"
        b"</BODY></HTML>\r\n"
    )


def cannot_execute() -> bytes:
    """构造 500 Internal Server Error 完整响应（含body）。
    
    对应 httpd.c: cannot_execute()
    触发条件：CGI脚本执行失败。
    """
    return (
        b"HTTP/1.0 500 Internal Server Error\r\n"
        + _CT_HTML
        + _SEP
        + b"<P>Error prohibited CGI execution.\r\n"
    )


def unimplemented() -> bytes:
    """构造 501 Method Not Implemented 完整响应（含body）。
    
    对应 httpd.c: unimplemented()
    触发条件：HTTP方法不是GET或POST。
    """
    return (
        b"HTTP/1.0 501 Method Not Implemented\r\n"
        + _SERVER
        + _CT_HTML
        + _SEP
        + b"<HTML><HEAD><TITLE>Method Not Implemented\r\n"
        b"</TITLE></HEAD>\r\n"
        b"<BODY><P>HTTP request method not supported.\r\n"
        b"</BODY></HTML>\r\n"
    )
