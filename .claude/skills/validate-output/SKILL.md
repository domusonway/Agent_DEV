# SKILL: validate-output
# 触发：所有模块单元测试 GREEN 后，进入集成验证
# 目的：确认模块组合后的行为符合整体规格

## 验证层级

### L1：单元层（各模块独立，已通过）
→ 跳过，继续 L2

### L2：集成层（模块间接口验证）

检查清单：
```
□ 模块 A 的输出类型 = 模块 B 期望的输入类型？
  验证：打印接口调用的实际类型，对比 BRIEF/SPEC

□ 错误传播路径正确？
  验证：故意传入非法输入，观察错误是否正确冒泡

□ 共享状态在模块边界的一致性？
  验证：并发写入后读取，确认无数据竞争
```

### L3：行为层（端到端功能验证）

对于网络服务类项目：
```python
# 标准行为测试骨架
import socket, threading

def test_end_to_end(host, port, request, expected):
    """端到端：发送请求，验证响应"""
    sock = socket.socket()
    sock.connect((host, port))
    sock.sendall(request)
    
    response = recv_all(sock)  # ★ MEM_F_C_004: 用精确版 recv_all
    sock.close()
    
    assert expected in response, f"期望 {expected!r}，得到 {response!r}"
```

### L4：边界层（压力和异常路径）

```
□ 并发 N 个连接同时操作（N 至少 10）
□ 超大输入（>单次 recv buffer）
□ 连接中途断开
□ 非法格式输入（协议错误）
```

## 验证失败处理

```
验证失败 → 确认是实现问题还是测试问题
  ↓
实现问题 → 回到对应模块修复（不改测试）
测试问题 → 记录原因，修正测试，重新走 RED→GREEN
  ↓
全部通过 → 触发 post-green hook → memory-update
```
