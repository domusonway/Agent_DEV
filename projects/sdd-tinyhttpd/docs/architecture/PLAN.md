# 全局规划（PLAN.md）— tinyhttpd Python重构

## 开发阶段
```
阶段 0: 框架初始化         ✅ 2026-03-03
阶段 1: 参考项目分析       ✅ 2026-03-03 (httpd.c 433行)
阶段 2: CONTEXT.md         ✅ 2026-03-03
阶段 3: 模块 SPEC          ✅ 2026-03-03
阶段 4: Fixtures/校验      🔨 进行中
阶段 5: TDD 实现           📋 待开始
阶段 6: 集成测试           📋
阶段 7: 经验沉淀文档       📋
```

## 模块拆分
| 模块 ID | 名称 | 优先级 | 依赖 | 状态 |
|---------|------|--------|------|------|
| M01 | response | P0 | - | ✏️ SPEC完成 |
| M02 | request_parser | P0 | - | ✏️ SPEC完成 |
| M03 | router | P1 | - | ✏️ SPEC完成 |
| M04 | static_handler | P1 | M01 | ✏️ SPEC完成 |
| M05 | cgi_handler | P1 | M01 | ✏️ SPEC完成 |
| M06 | server | P2 | M01-M05 | ✏️ SPEC完成 |

## 实现顺序（依赖拓扑）
M01 → M02 → M03 → M04 → M05 → M06

## 第三方依赖
| 库 | 版本 | 用途 |
|----|------|------|
| socket | 标准库 | TCP服务器 |
| threading | 标准库 | 每连接一线程 |
| subprocess | 标准库 | CGI执行 |
| os, stat | 标准库 | 文件系统操作 |
| pytest | 系统已有 | TDD测试 |

## fixture策略
- 非socket模块（response, router）：纯函数，直接调用，pickle输入/输出
- socket模块（request_parser, static_handler, cgi_handler）：使用MockSocket（BytesIO包装）
- server：端到端集成测试，实际socket对

**状态**: 📋待规划 ✏️规格中 🔨实现中 ✅通过 🔴失败
