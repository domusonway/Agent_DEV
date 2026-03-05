"""
request_parser.py — HTTP请求解析模块
对应 httpd.c: get_line(), accept_request()前半段, 消耗headers逻辑
"""
import socket

MAX_LINE = 4096


def get_line(sock: socket.socket) -> str:
    """
    从socket逐字节读取一行，标准化行结束符为\n。
    \r\n → \n, 单\r → \n, 单\n → \n
    连接关闭返回""。最多读MAX_LINE字节。
    """
    buf = []
    i = 0
    c = '\0'
    while i < MAX_LINE - 1 and c != '\n':
        data = sock.recv(1)
        if not data:
            break
        c = chr(data[0])
        if c == '\r':
            # peek下一个字节
            try:
                sock.setblocking(False)
                next_data = sock.recv(1)
                sock.setblocking(True)
                if next_data and chr(next_data[0]) == '\n':
                    c = '\n'
                elif next_data:
                    # 放回（无法真正放回，记录）
                    buf.append('\n')
                    buf.append(chr(next_data[0]))
                    i += 2
                    continue
                else:
                    c = '\n'
            except BlockingIOError:
                sock.setblocking(True)
                c = '\n'
        buf.append(c)
        i += 1
    return ''.join(buf)


def parse_request_line(line: str) -> tuple:
    """
    解析HTTP请求行。
    Returns: (method, url, protocol) — method大写
    Raises: ValueError 格式不合法
    """
    parts = line.strip().split()
    if len(parts) < 2:
        raise ValueError(f"Invalid request line: {line!r}")
    method = parts[0].upper()
    url = parts[1]
    protocol = parts[2] if len(parts) >= 3 else "HTTP/1.0"
    return method, url, protocol


def consume_headers(sock: socket.socket) -> dict:
    """
    读取并收集请求头，直到遇到空行。
    Returns: dict[header_name_lower → value]
    """
    headers = {}
    while True:
        line = get_line(sock)
        if not line or line == '\n':
            break
        if ':' in line:
            name, _, value = line.partition(':')
            headers[name.strip().lower()] = value.strip()
    return headers
