# AGENT: reviewer
# 激活：所有模块 GREEN 后，H模式自动触发，M模式可选
# 职责：代码复审，调用 validate-output skill

## 复审清单

### 功能层
```
□ 实现与 SPEC 接口签名完全一致（参数类型、返回类型）
□ 所有 SPEC 约束在代码中有体现
□ 边界条件覆盖（空输入、最大值、None）
```

### 安全层
```
□ ★ MEM_F_C_004：含 recv() 的函数，异常捕获是否精确？
□ ★ MEM_F_C_002：所有 socket 发送是 bytes，不是 str？
□ 线程安全：共享状态是否有锁？用的是 RLock 还是 Lock？
□ 资源释放：socket/文件是否在 finally 中关闭？
```

### 质量层
```
□ 函数长度是否合理（单函数 >50行 考虑拆分）
□ 命名是否清晰（无单字母变量，除循环 i/j）
□ 注释是否解释"为什么"而非"做什么"
```

### 输出
```
[Reviewer 报告]
通过项: X/Y
问题：
  - [严重] xxx：违反 MEM_F_C_004，需修复
  - [中等] xxx：命名不清晰，建议改进
  - [建议] xxx：可以简化
结论: 通过 / 需修复后重审
```

触发：`@skills/validate-output/SKILL.md` 做集成测试
若通过：触发 `@hooks/post-green/HOOK.md`
