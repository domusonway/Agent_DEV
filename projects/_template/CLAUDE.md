# 项目：[项目名]
# 创建日期：[YYYY-MM-DD]
# 框架版本：v3.0
# 框架根：../../  （相对于本文件的框架根路径）

---

## Step 0：AI 启动协议（每次对话开始必须执行）

```
1. 确认当前项目路径（对话中用户应已告知）
2. 读取本文件全部内容
3. 读取 CONTEXT.md（如已存在）
4. 输出确认语：
   "[已就绪] 项目: [项目名] | 强制规则: X 条已加载 | 模式: L/M/H"
```

如果 AI 没有输出确认语，用户应要求重新执行 Step 0。

---

## Step 1：复杂度评估

读取 `../../framework/skills/complexity-assess/SKILL.md` 并执行评估。

---

## ⚡ 强制规则（从 framework/memory/ 挑选后内联于此，≤5 条）

> 说明：以下规则从 framework/memory/INDEX.md 的 CRITICAL 列表中挑选，
> 根据项目类型选取适用规则，直接写在这里，AI 读本文件时必然看到。

<!-- 通用规则（所有项目保留） -->
1. **先写 SPEC 再写代码**，绝不先实现
2. **SPEC 必须明确接口 dtype**（bytes/str/int 不能模糊）
3. **测试失败只改实现**，禁止改断言或 skip

<!-- 网络项目追加（非网络项目删除第 4、5 条） -->
4. **recv() 必须用** `except (socket.timeout, ConnectionResetError, OSError)`，禁止 `except Exception`
5. **socket 发送必须是 bytes**；recv 返回 `b''` 表示连接关闭，必须 `if not data: break`

---

## 强制检查点

| 时机 | AI 必须执行的命令 | 用户验证方式 |
|------|----------------|------------|
| 写完任何网络代码后 | `bash ../../framework/hooks/pre-commit-check.sh ./modules/<模块名>/` | 查看输出是否全 ✅ |
| 所有测试 PASS 后 | `bash ../../framework/hooks/post-green.sh ./` | 查看 Memory 沉淀摘要 |

**AI 不展示检查点输出 = 检查点未执行，用户可直接要求重新执行。**

---

## 三种模式工作指南

### L 轻量模式（0–3 分）
- 写 `BRIEF.md`（≤15 行）代替 SPEC，只列接口签名+规则
- 单文件实现可接受
- 测试：5–10 个核心用例即可
- 无需 planner/reviewer

### M 标准模式（4–7 分）
- 写 `CONTEXT.md` + 每模块 `SPEC.md`（≤25 行）
- SPEC 中直接内联本模块相关的强制规则（从上方"强制规则"复制适用条目）
- 按依赖拓扑顺序实现，每模块完成即 TDD
- 可选：调用 `../../framework/agents/planner.md`

### H 完整模式（8+ 分）
- 完整 CONTEXT.md + 每模块 SPEC.md + docs/PLAN.md
- Planner → Implementer → Reviewer → Memory-Keeper 流水线
- 强制检查点不可跳过

---

## 项目隔离边界

- **代码**：仅在 `./modules/` 下，不引用其他项目代码
- **测试**：仅在 `./tests/` 下
- **Memory**：框架级 `../../framework/memory/`（只读），项目级 `./memory/`（可写）
- **跨项目参考**：查 `../../framework/memory/`，不直接读其他项目源码

---

## 运行环境

```bash
# 测试命令（根据环境选择）
python3 -m pytest modules/ -v
# 或（无 pytest 时）
python3 -m unittest discover -s modules -p "test_*.py" -v

# 检查脚本
bash ../../framework/hooks/pre-commit-check.sh ./modules/<模块名>/
bash ../../framework/hooks/post-green.sh ./
```

---

## 项目特有约束

> 在此填写此项目独有的规则，不适合放入框架 memory 的内容。
> 例如：特定的外部协议约定、业务逻辑约束、部署环境限制等。

（暂无，开发过程中按需填写）
