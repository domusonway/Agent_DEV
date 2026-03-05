---
module: router
version: 0.1.0
status: locked
---

# 模块规格 - router

> 职责：解析URL，构造文件系统路径，决定路由到static_handler还是cgi_handler

## 1. 职责
基于method、url和文件系统状态（stat），决定请求处理路径。

## 2. 接口定义

```python
def resolve_path(url: str, htdocs_root: str = "htdocs") -> tuple[str, str]:
    """
    将URL转换为文件系统路径，提取query_string。
    Args:
        url: 原始URL，如"/index.html"或"/cgi-bin/color.cgi?color=red"
        htdocs_root: 静态文件根目录（默认"htdocs"）
    Returns: (path, query_string)
        path: 文件系统路径，如"htdocs/index.html"，目录自动追加index.html
        query_string: URL中?后的部分，无则返回""
    """

def dispatch(client: socket.socket, method: str, url: str, htdocs_root: str = "htdocs") -> None:
    """
    完整路由逻辑：解析路径，检查文件状态，调用对应handler或错误响应。
    Args:
        client: 客户端socket
        method: 大写HTTP方法
        url: 原始URL（含可能的query_string）
        htdocs_root: 静态文件根目录
    """
```

### 输出规格 - resolve_path
| 返回 | 类型 | 说明 |
|------|------|------|
| path | str | 文件系统路径，目录追加/index.html |
| query_string | str | ?后内容，无则"" |

## 3. 行为约束
- url含"?"→分割，?前为路径，?后为query_string，method强制为CGI路由
- path末尾为"/"→追加"index.html"
- stat结果为目录→追加"/index.html"
- 文件不存在→consume剩余headers，send_not_found
- 文件有执行权限(os.X_OK)或method==POST→cgi_handler
- 否则→static_handler
- method不是GET/POST→send_unimplemented，不读取body

## 4. 参考项目对应
| 功能 | 参考位置 |
|------|---------|
| URL解析+路径构造 | httpd.c:51-127 accept_request |
| CGI判断逻辑 | httpd.c:102-125 |

## 5. 测试要点
- resolve_path: 普通URL、带query_string、目录URL、根URL"/"
- dispatch: GET静态文件、GET CGI(含?)、POST→CGI、文件不存在→404、DELETE→501

## 6. 依赖
- 依赖模块：request_parser, response, static_handler, cgi_handler
- 被依赖于：server
- 第三方库：os (标准库)
