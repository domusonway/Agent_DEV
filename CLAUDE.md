# SDD Framework · 主入口

> 版本: v1.0 | 验证项目: tinyhttpd + mini-redis(2×2对照实验)
> 设计原则: **复杂度驱动分流** · 轻量但有引导 · Memory预防优于事后修复

---

## 第一步：复杂度评估（收到任务后必须先做）

```
@skills/complexity-assess/SKILL.md
```

| 评分 | 模式 | 适用场景 | 框架开销 |
|------|------|---------|---------|
| 0–3分 | **L 轻量** | <300行, ≤2模块, 无网络/并发 | ~5% |
| 4–7分 | **M 标准** | 300–1500行, 3–6模块, 有网络/协议 | ~20–30% |
| 8+分  | **H 完整** | >1500行, 多人, 复杂状态/协议 | ~35–50% |

---

## 三种模式的核心差异

### L 轻量模式
- 写 `BRIEF.md`（≤15行）代替 SPEC，只列接口签名+规则
- Memory CRITICAL 规则直接内联进 BRIEF
- 单文件实现可接受，不强制模块拆分
- 测试：5–10个核心用例即可

### M 标准模式（**最常用**）
- `CONTEXT.md`（≤40行）+ 每模块 `SPEC.md`（≤25行）
- CONTEXT §3反模式**必须**内联 MEM_F_C_004 等 CRITICAL 规则
- 按依赖拓扑顺序实现，每模块完成即 TDD
- 调用 `@skills/tdd-cycle/SKILL.md` 获取标准模板

### H 完整模式
- 完整文档体系 + 多 Agent 协作
- Planner → Implementer → Reviewer → Memory-Keeper 流水线
- Hook 自动触发：网络代码 → network-guard，全绿 → post-green

---

## 框架级强制规则（所有模式通用）

1. **先明确再实现** — L写BRIEF，M/H写SPEC，绝不先写代码
2. **SPEC/BRIEF必含 dtype** — 所有接口明确参数和返回类型（MEM_F_C_002）
3. **测试失败只改实现** — 禁止改断言/skip（MEM_F_C_003）
4. **★ 网络代码必用精确异常** — `except (socket.timeout, ConnectionResetError, OSError)`
   禁用 `except Exception` 做 socket recv 捕获（MEM_F_C_004，实验验证有效）

---

## Memory 加载规则

每次启动先读：`@memory/INDEX.md`

Memory 命中检查（写每个模块前）：
- 对照 CRITICAL 列表，把适用的规则标注在 BRIEF/SPEC 对应位置（`★ MEM_F_C_00X`）
- **标注 = 预防**；未标注视为未命中，进入 network-guard 检查

---

## Agent 分工（H 模式 / M 模式可选调用）

```
@agents/planner.md      — 依赖拓扑分析，确定实现顺序
@agents/implementer.md  — 调用 tdd-cycle skill 逐模块实现
@agents/reviewer.md     — 调用 validate-output skill 复审
@agents/memory-keeper.md— 调用 memory-update skill 沉淀经验
```

---

## Hook 触发点

| 时机 | Hook | 作用 |
|------|------|------|
| 写任何 socket/recv/send 代码后 | `@hooks/network-guard/HOOK.md` | 强制检查 MEM_F_C_004 |
| 某模块 RED 超过 2 次仍未变 GREEN | `@hooks/stuck-detector/HOOK.md` | 触发 diagnose-bug |
| 所有测试 GREEN | `@hooks/post-green/HOOK.md` | validate-output + memory-update |
