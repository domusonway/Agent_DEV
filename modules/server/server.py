"""
modules/server/server.py
HTTP服务器主模块（集成层）

对应 httpd.c: startup(), accept_request(), main()
⚠️ 每连接一线程（threading.Thread，对应C版pthread_create）
⚠️ 全局状态：工作目录必须是含htdocs/的目录
"""
import socket
import threading
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.request_parser.request_parser import parse_request_line, drain_headers, parse_content_length
from modules.router.router import route
from modules.static_handler.static_handler import serve_file
from modules.cgi_handler.cgi_handler import execute_cgi
from modules.response.response import unimplemented, bad_request, not_found


def startup(port: int = 0):
    """创建并绑定TCP监听socket。
    
    对应 httpd.c: startup()
    
    Args:
        port: 监听端口，0表示系统自动分配
    Returns:
        (server_socket, actual_port)
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("", port))
    if port == 0:
        actual_port = server_sock.getsockname()[1]
    else:
        actual_port = port
    server_sock.listen(5)
    return server_sock, actual_port


def accept_request(conn: socket.socket, addr: tuple) -> None:
    """处理单个HTTP连接的完整请求-响应周期。
    
    对应 httpd.c: accept_request()
    
    流程：
    1. 解析请求行
    2. 校验method（只支持GET/POST）
    3. POST：解析Content-Length，读取body
    4. GET：drain请求头
    5. 路由：查找文件，判断CGI
    6. 分发：静态文件 or CGI执行
    7. 关闭连接
    """
    try:
        # Step 1：解析请求行
        req = parse_request_line(conn)
        method = req["method"]
        url = req["url"]
        query_string = req["query_string"]

        # Step 2：校验method
        if method not in ("GET", "POST"):
            conn.sendall(unimplemented())
            return

        # Step 3/4：处理请求头和body
        body = b""
        if method == "POST":
            content_length = parse_content_length(conn)
            if content_length == -1:
                conn.sendall(bad_request())
                return
            # 读取POST body
            body = b""
            remaining = content_length
            while remaining > 0:
                chunk = conn.recv(min(remaining, 4096))
                if not chunk:
                    break
                body += chunk
                remaining -= len(chunk)
        else:
            # GET：消耗剩余请求头
            drain_headers(conn)

        # Step 5：路由
        result = route(method, url, query_string)

        if not result["exists"]:
            conn.sendall(not_found())
            return

        # Step 6：分发
        if result["is_cgi"]:
            execute_cgi(conn, result["path"], method, query_string, body)
        else:
            serve_file(conn, result["path"])

    except Exception as e:
        # 线程内异常防止静默消失（见CONTEXT.md §3）
        try:
            conn.sendall(b"HTTP/1.0 500 Internal Server Error\r\n\r\n")
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_server(port: int = 4000) -> None:
    """启动HTTP服务器，循环accept连接，每连接一线程。
    
    对应 httpd.c: main()
    Ctrl+C退出。
    """
    server_sock, actual_port = startup(port)
    print(f"httpd running on port {actual_port}")

    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(
                target=accept_request,
                args=(conn, addr),
                daemon=True,
            )
            t.start()
    except KeyboardInterrupt:
        print("\nhttpd stopped.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    run_server()
