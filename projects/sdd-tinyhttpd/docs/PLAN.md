# 全局规划（PLAN.md）— sdd-tinyhttpd

## 开发阶段

```
阶段 0: 框架初始化（目录、CLAUDE.md）         ✅
阶段 1: 参考资料分析（C 版 tinyhttpd）        ✅
阶段 2: CONTEXT.md                           ✅
阶段 3: 全部模块 SPEC.md                      ✅
阶段 4: TDD 实现（M01→M06）                   📋
阶段 5: E2E 集成测试                          📋
阶段 6: 经验沉淀（post-green.sh）             📋
```

## 模块实现顺序

| 模块 ID | 名称 | 依赖 | 状态 |
|---------|------|------|------|
| M01 | response | - | 📋 |
| M02 | request_parser | - | 📋 |
| M03 | router | M02 | 📋 |
| M04 | static_handler | M01, M02 | 📋 |
| M05 | cgi_handler | M01, M02 | 📋 |
| M06 | server | M02, M03, M01 | 📋 |

M01 和 M02 可并行，M03/M04/M05 在 M01/M02 完成后并行。

## 高风险点

- M02 `get_line`：逐字节 recv，必须检查 b'' ★
- M05 `execute_cgi`：CGI 先验证再发状态行，禁 fork ★
- M06 `handle_client`：精确异常捕获，finally close ★
- M06 E2E：POST body 偏移（parse_content_length + drain_headers）★

**状态**: 📋待规划 ✏️规格中 🔨实现中 ✅通过 🔴失败
