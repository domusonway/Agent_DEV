"""
modules/cgi_handler/cgi_handler.py
CGI脚本执行模块

对应 httpd.c: execute_cgi()
⚠️ 用subprocess.Popen替代fork()+execl()（见MEM_D_HTTP_002）
⚠️ CGI输出全程bytes，直接sendall（见MEM_F_C_004）
"""
import os
import subprocess
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent))

from modules.response.response import cannot_execute


def execute_cgi(conn, path: str, method: str, query_string: str, body: bytes = b"") -> None:
    """执行CGI脚本，将输出发送给客户端。
    
    对应 httpd.c: execute_cgi()
    
    执行前先发送HTTP/1.0 200 OK（与C版一致，CGI脚本自己输出响应头）。
    环境变量：REQUEST_METHOD + QUERY_STRING(GET) 或 CONTENT_LENGTH(POST)
    
    Args:
        conn:         socket连接（需支持sendall）
        path:         CGI脚本文件系统路径
        method:       HTTP方法（"GET"或"POST"，大写）
        query_string: GET查询字符串（POST时为""）
        body:         POST请求体bytes（GET时为b""）
    """
    # 准备环境变量（继承当前进程环境，再叠加CGI变量）
    env = os.environ.copy()
    env["REQUEST_METHOD"] = method.upper()

    if method.upper() == "GET":
        env["QUERY_STRING"] = query_string
    else:  # POST
        env["CONTENT_LENGTH"] = str(len(body))

    # 预检：先确认脚本可执行（C版fork失败才发500，Python版提前检测）
    # 这避免了"先发200再发500"的头部混乱问题
    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        conn.sendall(cannot_execute())
        return

    # 先发送200状态行（与C版execute_cgi在fork前发送一致）
    conn.sendall(b"HTTP/1.0 200 OK\r\n")

    # 执行CGI脚本（subprocess替代fork+execl，见MEM_D_HTTP_002）
    try:
        proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, _stderr = proc.communicate(input=body)
        # 转发CGI输出给客户端
        conn.sendall(stdout)
    except OSError:
        # Popen启动失败（极少见，已通过预检）
        conn.sendall(cannot_execute())
