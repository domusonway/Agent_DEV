---
module: static_handler
version: 0.1.0
status: locked
---

# 模块规格：static_handler

> 参考: httpd.c — serve_file(), cat()

## 1. 职责
读取静态文件，发送 HTTP 200 响应头和文件内容到客户端 socket。

## 2. 接口定义

```python
def serve_file(conn: socket.socket, path: str) -> None
```

### 输入规格
| 参数 | 类型 | 说明 |
|------|------|------|
| conn | socket.socket | 已accept的客户端连接 |
| path | str | 文件系统路径（已由router解析，含htdocs前缀）|

### 输出规格
| 返回 | 类型 | 说明 |
|------|------|------|
| None | None | 副作用：向conn发送完整HTTP响应 |

## 3. 行为约束

### 正常流程
1. 用 `rb` 模式打开 path
2. 发送 ok_headers()（来自response模块）
3. 分块读取文件内容并 sendall（块大小：1024字节）
4. 关闭文件（使用with语句）

### 文件不存在
- 若 open() 抛出 FileNotFoundError/OSError → 调用 not_found(conn)（来自response模块）
- 注：router已做exists检查，此处是防御性处理

### 请求头消耗
⚠️ 参考C版serve_file()在发送响应前先drain请求头。
Python版：serve_file **不**负责drain，由server(accept_request)在调用前完成。
（此为模块间契约，见CONTEXT.md §5）

### 文件读取
- 使用 `rb`（二进制）模式，不解码，直接sendall bytes
- 分块读取避免大文件OOM：`while chunk := f.read(1024)`

## 4. 参考项目对应
| 功能 | 参考位置 | 备注 |
|------|---------|------|
| serve_file | httpd.c: serve_file() | Python版不含drain（已分离）|
| cat | httpd.c: cat() | 合并进serve_file，不单独暴露 |

## 5. 测试要点
- 正常: 发送文件内容，响应以ok_headers()内容开头
- 正常: 文件内容完整（不截断、不多余）
- 边界: 空文件 → 只发头部，body为空bytes
- 异常: 文件不存在 → 调用not_found响应
- 校验: 用mock socket(BytesIO)捕获sendall内容，断言头部+内容
- 校验基准: tests/fixtures/reference_static_handler_output.pkl

## 6. 依赖
- 依赖模块: response（ok_headers, not_found）
- 被依赖于: server(accept_request)
- 第三方库: socket（标准库）
