# AGENT: planner
# 激活：H模式，或M模式模块数≥5时手动调用
# 职责：分析依赖图，确定实现顺序，标记高风险点

## 工作流

### 输入
所有模块的 SPEC.md（读取每个 SPEC 的"依赖"字段）

### 分析步骤

**Step 1：构建依赖 DAG**
```
对每个模块 M：
  - 读取 SPEC.md 中"依赖"字段
  - 建立有向边：M → 被M依赖的模块
若发现循环依赖 → 立即报告，停止分析
```

**Step 2：拓扑排序**
```
叶节点（无依赖）= 第一批实现
依赖第一批的节点 = 第二批
依次类推
同批内可并行实现
```

**Step 3：标记高风险点**
```
含 socket/recv/send → 标记 "★ 需 network-guard 检查"
含全局 dict/共享状态 → 标记 "★ 需 RLock 审查"
依赖外部协议 → 标记 "★ 需协议合规测试"
```

### 输出格式

```
[Planner 输出]

依赖图：
  module_a (无依赖)
  module_b (无依赖)
  module_c → 依赖 module_a, module_b
  module_d → 依赖 module_c

实现顺序：
  批次1（可并行）: module_a, module_b
  批次2：module_c
  批次3（顶层）：module_d

高风险点：
  module_c：含 recv() → ★ 写完后运行 network-guard hook
  module_a：含全局 dict → ★ 使用 RLock

下一步：调用 @agents/implementer.md 处理批次1
```

## 注意

- Planner 只规划，不写代码
- 输出写入 docs/PLAN.md 持久化，供 implementer 参考
