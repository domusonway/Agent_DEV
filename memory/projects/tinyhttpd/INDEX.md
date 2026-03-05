# 项目记忆索引
# 项目: tinyhttpd (Python重构)

> 只记"此项目特有、换个项目就不适用"的经验
> 通用经验写到 memory/framework/ 或 memory/domains/

## CRITICAL（项目特有，强制加载）
_(随Bug修复积累)_

## IMPORTANT — 项目特有约束
| ID | 标题 | 任务类型 | 文件 |
|----|------|---------|------|
_(待填充)_

## IMPORTANT — Bug 修复经验
| ID | 发现于 | 根因摘要 | 文件 |
|----|--------|---------|------|
| MEM_P_TINYHTTPD_001 | cgi_handler TDD | CGI需先验证可执行性再发200，否则头部混乱 | [→](MEM_P_TINYHTTPD_001.md) |

_记录数: 1 | 创建: 2026-03-03_
