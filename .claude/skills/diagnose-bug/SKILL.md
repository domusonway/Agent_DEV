# SKILL: diagnose-bug
# 触发：RED 超过 2 次仍未 GREEN，或出现意外 ERROR（非 FAIL）

## 诊断步骤（按顺序执行）

### Step 1：区分 FAIL vs ERROR
```
FAIL  = 断言失败（逻辑错误，预期行为不符）
ERROR = 异常未捕获（代码崩溃，接口错误）
→ ERROR 优先于 FAIL 处理
```

### Step 2：ERROR 时的检查清单

```
□ 是 ConnectionResetError / OSError？
  → ★ MEM_F_C_004：recv 循环缺少精确异常捕获
  → 修复：except (socket.timeout, ConnectionResetError, OSError)

□ 是 TypeError: a bytes-like object is required?
  → ★ MEM_F_C_002：str 直接传给 socket.send()
  → 修复：所有发送内容必须 .encode() 为 bytes

□ 是 AttributeError: NoneType?
  → 函数返回 None 但调用方期望其他类型
  → 检查 BRIEF/SPEC 中的返回类型标注

□ 是 RecursionError / 测试卡住不退出？
  → threading.Lock 在同一线程递归调用 → 死锁
  → 修复：改用 threading.RLock
```

### Step 3：FAIL 时的检查清单

```
□ 测试的断言是否和 BRIEF/SPEC 一致？
  → 若不一致：BRIEF/SPEC 定义为准（不改断言，改实现）

□ 是否存在状态泄漏（上一个测试影响了这个）？
  → 在 setUp() 中重置所有共享状态

□ 是否是浮点精度问题？
  → 用 assertAlmostEqual 或整数化处理

□ 是否是 CRLF vs LF 问题？
  → 所有协议输出用 \r\n，测试断言也用 \r\n
```

### Step 4：输出诊断报告

```
[Bug诊断报告]
症状: FAIL / ERROR
错误信息: <粘贴错误>
根因: <从上面清单中定位>
关联Memory: MEM_F_C_00X（若匹配）
修复方案: <具体代码修改>
是否修改测试: 否（除非确认测试本身有bug）
```

## 常见根因速查表

| 错误 | 根因 | Memory | 修复 |
|------|------|--------|------|
| ConnectionResetError | recv 未精确捕获 | MEM_F_C_004 | 精确 except 三元组 |
| TypeError bytes | str→socket | MEM_F_C_002 | .encode() |
| 测试永远 PASS | 测试写错了 | MEM_F_C_001 | 先确认 RED |
| 断言值硬改 | 违反规则 | MEM_F_C_003 | 改实现不改测试 |
| 死锁 | Lock 递归 | — | 改 RLock |
