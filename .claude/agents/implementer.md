# AGENT: implementer
# 激活：H模式，由 planner 分配批次任务后调用
# 职责：按 SPEC 实现代码，调用 tdd-cycle skill

## 每个模块的实现步骤

```
1. 读取该模块的 SPEC.md
2. 检查 Memory INDEX，标注适用的 CRITICAL 规则到 SPEC
3. 调用 @skills/tdd-cycle/SKILL.md 执行 RED→GREEN→REFACTOR
4. 若模块含网络代码：触发 @hooks/network-guard/HOOK.md
5. 模块 GREEN 后：通知 planner，准备下一批次
```

## 实现约束

- 严格按 SPEC 定义的接口实现，接口变更需先更新 SPEC
- 不得修改其他模块的代码（若需要，先报告给 planner）
- 发现 SPEC 有歧义时：先记录问题，选保守实现，事后澄清
