# HOOK: post-green
# 触发：当前模块/项目所有测试变 GREEN
# 目的：自动推进到验证和经验沉淀，不靠人工记得

## 触发序列

```
所有测试 GREEN
    │
    ├─ 1. 检查 Memory 标注覆盖率
    │      扫描代码中 "★ MEM" 注释数量
    │      若有 recv() 但无任何 ★ MEM_F_C_004 → 警告
    │
    ├─ 2. 调用 validate-output skill（集成验证）
    │      @skills/validate-output/SKILL.md
    │      若失败 → 回到实现，不是改测试
    │
    └─ 3. 判断是否有新发现值得写入 Memory
           有新 Bug 模式 / 新决策理由 → @skills/memory-update/SKILL.md
           无新发现 → 跳过，完成
```

## 快速检查脚本

```bash
#!/bin/bash
# post-green.sh — 在项目根目录运行

echo "=== post-green 检查 ==="

# 1. Memory 标注覆盖
MEM_COUNT=$(grep -r "★ MEM" . --include="*.py" -l | wc -l)
RECV_COUNT=$(grep -r "recv(" . --include="*.py" -l | wc -l)

if [ "$RECV_COUNT" -gt 0 ] && [ "$MEM_COUNT" -eq 0 ]; then
    echo "⚠️  警告：发现 recv() 调用但无 ★ MEM_F_C_004 标注"
    echo "   请确认异常处理是否符合 MEM_F_C_004"
else
    echo "✅ Memory 标注：$MEM_COUNT 文件有标注"
fi

# 2. 运行集成测试（若有）
if [ -f "tests/test_integration.py" ]; then
    echo "--- 集成测试 ---"
    python3 -m pytest tests/test_integration.py -v
fi

echo "=== 完成 ==="
```
