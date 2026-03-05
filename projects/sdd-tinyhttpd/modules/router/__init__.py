"""
router.py — HTTP请求路由
对应 httpd.c: accept_request()中的路由决策逻辑
"""
import socket
import os
from modules.request_parser import consume_headers
from modules.response import send_not_found, send_unimplemented
from modules.static_handler import serve_file
from modules.cgi_handler import execute_cgi


def resolve_path(url: str, htdocs_root: str = "htdocs") -> tuple:
    """
    将URL转换为文件系统路径，提取query_string。
    Returns: (path, query_string, is_cgi_by_url)
    """
    query_string = ""
    is_cgi_by_url = False

    # 分割query string
    if '?' in url:
        url_path, query_string = url.split('?', 1)
        is_cgi_by_url = True
    else:
        url_path = url

    # 构造文件系统路径
    path = htdocs_root + url_path

    # 目录→追加index.html
    if path.endswith('/'):
        path += "index.html"

    return path, query_string, is_cgi_by_url


def dispatch(client: socket.socket, method: str, url: str, htdocs_root: str = "htdocs") -> None:
    """
    完整路由逻辑：解析路径，检查文件状态，调用对应handler。
    """
    # 不支持的方法
    if method not in ('GET', 'POST'):
        send_unimplemented(client)
        return

    path, query_string, is_cgi_by_url = resolve_path(url, htdocs_root)

    # POST直接走CGI
    cgi = (method == 'POST') or is_cgi_by_url

    # 检查文件是否存在
    if not os.path.exists(path):
        consume_headers(client)
        send_not_found(client)
        return

    # 目录→追加index.html
    if os.path.isdir(path):
        path = path.rstrip('/') + '/index.html'
        if not os.path.exists(path):
            consume_headers(client)
            send_not_found(client)
            return

    # 检查执行权限→CGI
    if os.access(path, os.X_OK):
        cgi = True

    if cgi:
        execute_cgi(client, path, method, query_string)
    else:
        serve_file(client, path)
