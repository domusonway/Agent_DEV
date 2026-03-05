---
module: router
version: 0.1.0
status: locked
---

# 模块规格：router

> 参考: httpd.c — accept_request() 中的路由判断部分（stat检查、CGI判断）

## 1. 职责
根据请求信息确定路由结果：文件路径解析、是否需要CGI、文件是否存在。

## 2. 接口定义

```python
def resolve_path(url: str) -> str
def should_use_cgi(path: str, method: str, query_string: str) -> bool
def route(method: str, url: str, query_string: str) -> dict
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| url | str | URL路径，如"/index.html"或"/cgi-bin/script" |
| method | str | HTTP方法，"GET"或"POST" |
| query_string | str | URL中?后的部分，或"" |
| path | str | 文件系统路径（已含htdocs前缀）|

### 输出规格
| 函数 | 返回类型 | 说明 |
|------|---------|------|
| resolve_path | str | 完整文件系统路径（含htdocs前缀，已处理目录和index.html）|
| should_use_cgi | bool | True=执行CGI，False=静态文件 |
| route | dict | 完整路由结果 |

### route() 返回字段
| 字段 | 类型 | 说明 |
|------|------|------|
| path | str | 解析后的文件系统路径 |
| exists | bool | 文件是否存在（stat成功）|
| is_cgi | bool | 是否使用CGI |
| method | str | 原样透传 |
| query_string | str | 原样透传 |

## 3. 行为约束

### resolve_path 规则（严格按C版）
1. `path = "htdocs" + url`
2. 若 path 末尾是 '/'，追加 "index.html"
3. 若 stat(path) 是目录（S_IFDIR），追加 "/index.html"
4. 返回最终路径

### should_use_cgi 规则（三条任一触发）
1. method == "POST"
2. query_string != ""（GET带?）
3. 文件有任意执行权限：`os.access(path, os.X_OK)`

### route() 综合逻辑
1. resolve_path(url) → path
2. os.path.exists(path) → exists
3. if not exists: return {exists:False, is_cgi:False, ...}
4. should_use_cgi(path, method, query_string) → is_cgi
5. return 完整dict

### 路径安全
- 必须防路径穿越：解析后path必须以"htdocs"开头
- 若检测到穿越（path不以"htdocs"开头），exists=False

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| resolve_path | httpd.c: accept_request() sprintf/strcat部分 | |
| should_use_cgi | httpd.c: accept_request() cgi=1的三个条件 | |
| route | httpd.c: accept_request() stat到cgi判断 | 提取为独立函数 |

## 5. 测试要点
- resolve_path("/") → "htdocs/index.html"
- resolve_path("/index.html") → "htdocs/index.html"
- resolve_path("/sub/") → "htdocs/sub/index.html"
- should_use_cgi("htdocs/file", "POST", "") → True
- should_use_cgi("htdocs/file", "GET", "q=1") → True
- should_use_cgi("htdocs/file.html", "GET", "") → False（假设无执行权限）
- route: 路径穿越"/../etc/passwd" → exists=False
- 校验基准: tests/fixtures/reference_router_output.pkl

## 6. 依赖
- 依赖模块: 无（纯文件系统操作）
- 被依赖于: server(accept_request)
- 第三方库: os, os.path, stat（标准库）
