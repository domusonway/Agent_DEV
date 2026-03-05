"""
modules/router/router.py
HTTP请求路由模块

对应 httpd.c: accept_request()中的路由判断部分
纯文件系统操作，无网络代码。
"""
import os
import os.path


def resolve_path(url: str) -> str:
    """将URL解析为文件系统路径。
    
    对应 httpd.c: accept_request()中的sprintf/strcat部分
    规则：
    1. path = "htdocs" + url
    2. 末尾是/ → 追加 index.html  
    3. 是目录 → 追加 /index.html
    """
    # 规则1：拼接htdocs前缀
    path = "htdocs" + url

    # 规则2：URL末尾是/时追加index.html
    if path.endswith("/"):
        path += "index.html"

    # 规则3：路径是目录时追加/index.html
    if os.path.isdir(path):
        path = path.rstrip("/") + "/index.html"

    return path


def should_use_cgi(path: str, method: str, query_string: str) -> bool:
    """判断请求是否应走CGI路由。
    
    对应 httpd.c: accept_request()中的cgi=1的三个判断条件
    三条任一为True则走CGI：
    1. POST请求
    2. GET带查询字符串（?）
    3. 文件有执行权限
    """
    # 条件1：POST
    if method.upper() == "POST":
        return True

    # 条件2：有query_string（GET带?）
    if query_string:
        return True

    # 条件3：文件有执行权限（任意：owner/group/other）
    if os.access(path, os.X_OK):
        return True

    return False


def route(method: str, url: str, query_string: str) -> dict:
    """综合路由函数，返回完整路由结果。
    
    对应 httpd.c: accept_request()从stat到CGI判断的完整逻辑
    """
    # 解析路径
    path = resolve_path(url)

    # 路径安全检查：防止路径穿越（../）
    # 规范化后路径必须以htdocs开头
    abs_path = os.path.normpath(path)
    abs_htdocs = os.path.normpath("htdocs")
    if not abs_path.startswith(abs_htdocs):
        return {
            "path": path,
            "exists": False,
            "is_cgi": False,
            "method": method,
            "query_string": query_string,
        }

    # 检查文件是否存在
    exists = os.path.exists(path)

    if not exists:
        return {
            "path": path,
            "exists": False,
            "is_cgi": False,
            "method": method,
            "query_string": query_string,
        }

    # 判断CGI
    is_cgi = should_use_cgi(path, method, query_string)

    return {
        "path": path,
        "exists": True,
        "is_cgi": is_cgi,
        "method": method,
        "query_string": query_string,
    }
