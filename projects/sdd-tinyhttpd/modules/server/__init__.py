"""
server.py — HTTP服务器主循环
对应 httpd.c: startup(), main(), accept_request()顶层
"""
import socket
import threading
import sys
from modules.request_parser import get_line, parse_request_line
from modules.router import dispatch


def startup(port: int = 0) -> tuple:
    """
    创建TCP监听socket。
    Returns: (server_socket, actual_port)
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', port))
    server_sock.listen(5)
    actual_port = server_sock.getsockname()[1]
    return server_sock, actual_port


def accept_request(client_sock: socket.socket, htdocs_root: str = "htdocs") -> None:
    """
    处理单个HTTP请求（在线程中调用）。
    解析请求行→dispatch→close socket。
    """
    try:
        line = get_line(client_sock)
        if not line or line == '\n':
            return  # 空请求，忽略
        try:
            method, url, _ = parse_request_line(line)
        except ValueError:
            return  # 格式错误，忽略
        dispatch(client_sock, method, url, htdocs_root)
    except Exception as e:
        # 记录错误但不崩溃
        print(f"[server] Error handling request: {e}", file=sys.stderr)
    finally:
        try:
            client_sock.close()
        except Exception:
            pass


def run(port: int = 0, htdocs_root: str = "htdocs") -> None:
    """
    启动HTTP服务器主循环（阻塞）。
    """
    server_sock, actual_port = startup(port)
    print(f"httpd running on port {actual_port}")
    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            t = threading.Thread(
                target=accept_request,
                args=(client_sock, htdocs_root),
                daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        print("\nhttpd stopped.")
    finally:
        server_sock.close()
