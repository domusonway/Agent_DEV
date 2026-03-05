"""
modules/request_parser/request_parser.py
HTTP/1.0 请求解析模块

对应 httpd.c: get_line(), accept_request()的请求行解析部分
⚠️ socket数据全程bytes，只在返回时decode（见MEM_F_C_004）
⚠️ recv返回b''表示连接关闭（见MEM_F_C_005）
"""
import socket as _socket


def get_line(conn) -> str:
    """从socket读取一行，返回规范化字符串（含\\n，不含\\r）。
    
    对应 httpd.c: get_line()
    - \\r\\n → \\n
    - 裸\\n → \\n  
    - 连接关闭 → ""
    最大行长：1024字节（与C版buf大小一致）
    """
    buf = b""
    while len(buf) < 1024:
        c = conn.recv(1)
        if not c:           # 连接关闭（见MEM_F_C_005）
            break
        if c == b"\r":
            # peek下一个字节
            next_c = conn.recv(1)
            if next_c == b"\n":
                buf += b"\n"
            elif not next_c:
                buf += b"\n"   # 连接关闭，视为行结束
            else:
                # 裸\r（罕见），视为\n，next_c已消耗需退回
                # 简化：丢弃next_c，这在HTTP请求中极罕见
                buf += b"\n"
            break
        if c == b"\n":
            buf += c
            break
        buf += c
    return buf.decode("utf-8", errors="replace")


def parse_request_line(conn) -> dict:
    """解析HTTP请求行，返回method/url/query_string。
    
    对应 httpd.c: accept_request()前半部分
    GET /path?qs HTTP/1.0 → {method:"GET", url:"/path", query_string:"qs"}
    POST /path HTTP/1.0   → {method:"POST", url:"/path", query_string:""}
    """
    line = get_line(conn).rstrip("\n")
    parts = line.split()
    if len(parts) < 2:
        return {"method": "", "url": "/", "query_string": ""}

    method = parts[0].upper()
    raw_url = parts[1]

    # 提取query_string（GET带?时分割）
    if method == "GET" and "?" in raw_url:
        url, query_string = raw_url.split("?", 1)
    else:
        url = raw_url
        query_string = ""

    return {
        "method": method,
        "url": url,
        "query_string": query_string,
    }


def drain_headers(conn) -> None:
    """消耗所有请求头直到空行（\\r\\n），不返回。
    
    对应 httpd.c: serve_file()和execute_cgi()内的drain循环
    空行在get_line规范化后为"\\n"
    """
    while True:
        line = get_line(conn)
        if not line or line == "\n":
            break


def parse_content_length(conn) -> int:
    """从请求头中解析Content-Length值。
    
    对应 httpd.c: execute_cgi()内的头部解析
    找到返回int值，未找到返回-1，读到空行停止。
    """
    while True:
        line = get_line(conn)
        if not line or line == "\n":
            return -1
        # 大小写不敏感匹配（见HTTP RFC）
        if line.lower().startswith("content-length:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return -1
