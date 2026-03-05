# SDD Framework — Tinyhttpd Python Reconstruction

> 通用框架层规则 + Tinyhttpd 项目入口

## 框架核心约束
1. **不复制参考代码** — C代码仅用于理解行为，Python实现必须独立编写
2. **测试失败只改实现** — 改测试掩盖问题
3. **先写 SPEC 再写代码** — 没有规格的实现无法被验证
4. **fixture基准 = 协议正确性** — 不是与C字节级别相同，而是HTTP协议行为正确

## 项目导航
- 项目上下文：@projects/tinyhttpd/CONTEXT.md
- 记忆索引：@memory/INDEX.md
- 开发计划：@docs/architecture/PLAN.md
- 任务追踪：@docs/architecture/TODO.md

## Agent 调用
- 分析/规划 → @planner
- TDD实现 → @implementer  
- 生成fixtures/校验 → @tester
- 代码复审 → @reviewer
- Bug诊断 → @diagnostician

## 运行环境
```bash
python3   # 系统Python3，标准库only（socket, threading, subprocess, os, stat）
python3 -m pytest modules/ -v
python3 tests/run_all_validators.py
```
