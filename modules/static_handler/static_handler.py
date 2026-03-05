"""
modules/static_handler/static_handler.py
静态文件服务模块

对应 httpd.c: serve_file(), cat()
⚠️ 文件用rb模式读取，直接sendall bytes，不decode（见MEM_F_C_004）
⚠️ 调用者（server）负责在调用前drain请求头（见CONTEXT.md §5）
"""
import sys
import os
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent))

from modules.response.response import ok_headers, not_found as _not_found

_CHUNK_SIZE = 1024  # 与C版buf大小一致


def serve_file(conn, path: str) -> None:
    """读取静态文件，发送HTTP 200响应+文件内容。
    
    对应 httpd.c: serve_file() + cat()
    - 文件不存在：发送404
    - 文件内容：rb模式分块读取，直接sendall（不decode）
    
    Args:
        conn: socket连接对象（需支持sendall）
        path: 文件系统路径（由router提供，已含htdocs前缀）
    """
    try:
        f = open(path, "rb")
    except (FileNotFoundError, OSError, PermissionError):
        # 防御性处理：router已做exists检查，此处处理边缘情况
        conn.sendall(_not_found())
        return

    with f:
        # 发送200响应头
        conn.sendall(ok_headers(path))
        # 分块读取并发送文件内容（对应C版cat()）
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)
