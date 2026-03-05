# Memory INDEX — SDD Framework v2
# 每次启动必读，按任务类型加载对应记忆

## ⚡ CRITICAL（所有任务必加载）

| ID | 标题 | 适用场景 | 路径 |
|----|------|---------|------|
| MEM_F_C_001 | 校验器必须先自测 | validation | framework/critical/MEM_F_C_001.md |
| MEM_F_C_002 | SPEC/BRIEF 必须含 dtype | spec_writing | framework/critical/MEM_F_C_002.md |
| MEM_F_C_003 | 禁止修改测试用例 | tdd_impl | framework/critical/MEM_F_C_003.md |
| **MEM_F_C_004** | **socket recv 必须精确捕获异常** | **network_code** | framework/critical/MEM_F_C_004.md |

> **v2 新增说明**：MEM_F_C_004 现在通过两个机制强制生效：
> 1. CONTEXT.md §3 反模式模板内置此规则
> 2. network-guard hook 在写完网络代码后自动检查

## 加载规则

| 任务类型 | 必加载 | 可选加载 |
|---------|--------|---------|
| 任何任务 | CRITICAL 全部 | — |
| 网络/TCP服务器 | + network-guard hook | domains/networking/ |
| 跨语言重构 | + MEM_F_I_005 | domains/cross-lang/ |
| 纯算法/工具 | CRITICAL 即可 | — |

## 框架版本历史

| 版本 | 日期 | 关键改进 |
|------|------|---------|
| v1.0 | 2026-03-03 | tinyhttpd 实验，发现 MEM_F_C_004 |
| v2.0 | 2026-03-04 | 复杂度分流（L/M/H）；所有 skill/agent/hook 补全；MEM_F_C_004 内置到框架级；数据校准 D1-D5 |

_记录总数：4 CRITICAL | 下次审查：2026-09-04_
