---
module: [模块名]
version: 0.1.0
status: draft  # draft → locked（实现前锁定）
---

# 模块规格：[模块名]

> 参考：[对应的参考实现位置]

## 1. 职责（单一职责原则）

[一句话描述，不超过 30 字]

## 2. 接口定义

```python
def function_name(param: Type) -> ReturnType:
    """[一句话说明]"""
```

### 输入规格

| 参数 | 类型 | 说明 |
|------|------|------|
| param | Type | [说明] |

### 输出规格

| 返回 | 类型 | 说明 |
|------|------|------|
| result | bytes | [说明，类型必须精确] |

## 3. 行为约束

[列出所有边界条件和约束，这是实现的唯一依据]

## 4. ⚠️ 本模块强制规则

> 从 CLAUDE.md 强制规则中复制适用于本模块的条目，内联在此。
> AI 读 SPEC 时必然看到，不需要额外"加载 memory"。

<!-- 示例（网络模块）：
- recv() 必须用 `except (socket.timeout, ConnectionResetError, OSError)`
- 所有 sendall 参数必须是 bytes，不是 str
- recv 返回 b'' 表示连接关闭，必须 `if not data: break`
-->

## 5. 测试要点

- [正常用例1]
- [正常用例2]
- [边界用例]
- [异常用例]

## 6. 依赖

- 依赖模块：[无 / 模块名]
- 被依赖于：[模块名]
- 第三方库：[标准库名]
