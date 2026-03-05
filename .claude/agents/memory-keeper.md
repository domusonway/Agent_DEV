# AGENT: memory-keeper
# 激活：项目完成后（所有测试 GREEN + Reviewer 通过）
# 职责：沉淀本项目经验到 Memory，更新 INDEX

## 工作流

```
1. 收集本项目的 Bug 记录（若有记录的话）
2. 调用 @skills/memory-update/SKILL.md
   → 判断哪些经验值得写入
   → 按格式写入对应 memory/ 目录
3. 更新 memory/INDEX.md
4. 输出本项目记忆沉淀摘要
```

## 输出格式

```
[Memory-Keeper 报告]

本项目新增记忆：
  - MEM_F_C_XXX：[标题]（CRITICAL）
  - MEM_F_I_XXX：[标题]（IMPORTANT）

验证有效的旧记忆（命中）：
  - MEM_F_C_004：在 [模块名] 预防了 ConnectionResetError ✅

未命中的旧记忆：
  - [若有，分析原因]

Memory 总量：X CRITICAL + Y IMPORTANT
下次项目应重点关注：[基于本次经验的提醒]
```
