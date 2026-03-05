---
id: MEM_F_I_004
title: 无网络环境下SDD框架须用unittest替代pytest
tags:
  domain: general
  lang_stack: python
  task_type: tdd_impl
  severity: IMPORTANT
created: 2026-03-03
expires: 2027-03-03
confidence: high
---

## 经验
SDD框架SKILL.md中的pytest命令在无网络环境（pip不可用）下无法使用。
Python标准库的unittest是完全可行的替代方案，无需安装。

## 环境检测
```bash
python3 -m pytest --version 2>/dev/null || echo "需要用unittest"
python3 -m unittest --help >/dev/null && echo "unittest可用"
```

## 替换方式
| pytest用法 | unittest替代 |
|-----------|------------|
| `pytest modules/ -v` | `python3 -m unittest discover -s modules -p "test_*.py" -v` |
| `pytest test_foo.py -v` | `python3 -m unittest test_foo -v` |
| `@pytest.fixture` | `setUp/tearDown` 方法 |
| `pytest.raises(X)` | `self.assertRaises(X)` |

## 框架改进建议
SKILL.md中所有pytest命令应改为：
```bash
python3 -m pytest modules/ -v 2>/dev/null || \
  python3 -m unittest discover -s modules -p "test_*.py" -v
```
或在CONTEXT.md §2中明确指定测试框架命令。
