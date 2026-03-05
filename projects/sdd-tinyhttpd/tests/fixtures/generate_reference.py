"""
tests/fixtures/generate_reference.py
基于HTTP协议正确性生成TDD基准输出

用法:
  python3 tests/fixtures/generate_reference.py --module response
  python3 tests/fixtures/generate_reference.py --all
"""
import argparse, pickle, sys, io, os, stat, tempfile
from pathlib import Path

FIXTURES = Path(__file__).parent
FIXTURES.mkdir(exist_ok=True)

def get_modules():
    return ["response", "request_parser", "router", "static_handler", "cgi_handler"]

# ── M01: response ──────────────────────────────────────────────────
def generate_response():
    """基于HTTP/1.0协议标准定义正确输出"""
    SERVER = b"Server: jdbhttpd/0.1.0\r\n"
    CT_HTML = b"Content-Type: text/html\r\n"
    SEP = b"\r\n"

    outputs = {
        "ok_headers": (
            b"HTTP/1.0 200 OK\r\n" + SERVER + CT_HTML + SEP
        ),
        "bad_request": (
            b"HTTP/1.0 400 BAD REQUEST\r\n" + CT_HTML + SEP +
            b"<P>Your browser sent a bad request, "
            b"such as a POST without a Content-Length.\r\n"
        ),
        "not_found": (
            b"HTTP/1.0 404 NOT FOUND\r\n" + SERVER + CT_HTML + SEP +
            b"<HTML><TITLE>Not Found</TITLE>\r\n"
            b"<BODY><P>The server could not fulfill\r\n"
            b"your request because the resource specified\r\n"
            b"is not found on the server.\r\n"
            b"</BODY></HTML>\r\n"
        ),
        "cannot_execute": (
            b"HTTP/1.0 500 Internal Server Error\r\n" + CT_HTML + SEP +
            b"<P>Error prohibited CGI execution.\r\n"
        ),
        "unimplemented": (
            b"HTTP/1.0 501 Method Not Implemented\r\n" + SERVER + CT_HTML + SEP +
            b"<HTML><HEAD><TITLE>Method Not Implemented\r\n"
            b"</TITLE></HEAD>\r\n"
            b"<BODY><P>HTTP request method not supported.\r\n"
            b"</BODY></HTML>\r\n"
        ),
    }
    return {"inputs": {}, "outputs": outputs}

# ── M02: request_parser ────────────────────────────────────────────
def generate_request_parser():
    """使用bytes流模拟socket，定义解析结果"""
    cases = {
        "get_simple": {
            "raw": b"GET /index.html HTTP/1.0\r\n",
            "expected": {"method": "GET", "url": "/index.html", "query_string": ""}
        },
        "get_with_query": {
            "raw": b"GET /cgi?name=foo&bar=1 HTTP/1.0\r\n",
            "expected": {"method": "GET", "url": "/cgi", "query_string": "name=foo&bar=1"}
        },
        "post": {
            "raw": b"POST /submit HTTP/1.0\r\n",
            "expected": {"method": "POST", "url": "/submit", "query_string": ""}
        },
        "get_line_crlf": {
            "raw": b"Hello World\r\n",
            "expected_line": "Hello World\n"
        },
        "get_line_lf": {
            "raw": b"Hello\n",
            "expected_line": "Hello\n"
        },
        "content_length": {
            "raw": b"Content-Type: text/plain\r\nContent-Length: 42\r\n\r\n",
            "expected_cl": 42
        },
        "no_content_length": {
            "raw": b"Content-Type: text/plain\r\n\r\n",
            "expected_cl": -1
        },
    }
    return {"cases": cases}

# ── M03: router ────────────────────────────────────────────────────
def generate_router():
    """路由规则验证，基于文件系统"""
    cases = {
        "resolve_root": {
            "url": "/",
            "expected_path": "htdocs/index.html"
        },
        "resolve_file": {
            "url": "/about.html",
            "expected_path": "htdocs/about.html"
        },
        "resolve_subdir": {
            "url": "/sub/",
            "expected_path": "htdocs/sub/index.html"
        },
        "cgi_post": {
            "path": "htdocs/any", "method": "POST", "qs": "",
            "expected_cgi": True
        },
        "cgi_query": {
            "path": "htdocs/any", "method": "GET", "qs": "q=1",
            "expected_cgi": True
        },
        "static": {
            "path": "htdocs/index.html", "method": "GET", "qs": "",
            "expected_cgi": False  # 假设无执行权限
        },
        "path_traversal": {
            "url": "/../etc/passwd",
            "expect_blocked": True
        },
    }
    return {"cases": cases}

# ── M04: static_handler ────────────────────────────────────────────
def generate_static_handler():
    """静态文件服务：使用临时文件验证"""
    test_content = b"<html><body>Hello World</body></html>\n"
    SERVER = b"Server: jdbhttpd/0.1.0\r\n"
    CT_HTML = b"Content-Type: text/html\r\n"
    ok_headers = b"HTTP/1.0 200 OK\r\n" + SERVER + CT_HTML + b"\r\n"

    return {
        "test_content": test_content,
        "expected_response": ok_headers + test_content,
        "ok_headers": ok_headers,
    }

# ── M05: cgi_handler ───────────────────────────────────────────────
def generate_cgi_handler():
    """CGI执行：使用python3 -c echo脚本"""
    return {
        "cgi_output_prefix": b"HTTP/1.0 200 OK\r\n",
        "env_keys_get": ["REQUEST_METHOD", "QUERY_STRING"],
        "env_keys_post": ["REQUEST_METHOD", "CONTENT_LENGTH"],
    }

# ── 主逻辑 ─────────────────────────────────────────────────────────
GENERATORS = {
    "response": generate_response,
    "request_parser": generate_request_parser,
    "router": generate_router,
    "static_handler": generate_static_handler,
    "cgi_handler": generate_cgi_handler,
}

def generate(module: str):
    print(f"\n── Fixture: {module} ──")
    data = GENERATORS[module]()
    out_path = FIXTURES / f"reference_{module}_output.pkl"
    out_path.write_bytes(pickle.dumps(data))
    print(f"✅ 已保存 {out_path.name}")
    return data

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--module")
    p.add_argument("--all", action="store_true")
    args = p.parse_args()
    if args.all:
        for m in get_modules():
            generate(m)
    elif args.module:
        generate(args.module)
    else:
        p.print_help()
