# 项目记忆索引
# 项目: tinyhttpd — Python重构

## CRITICAL（项目特有）
| ID | 标题 | 文件 |
|----|------|------|
| MEM_P_TH_001 | socketpair测试需捕获ConnectionResetError | MEM_P_TH_001.md |
| MEM_P_TH_002 | C源码无法直接生成fixture，需重新定义基准策略 | MEM_P_TH_002.md |

## IMPORTANT — Bug修复经验
| ID | 描述 | 根因 |
|----|------|------|
| BUG-001 | router测试ConnectionResetError | recv_all未捕获OSError |
| BUG-002 | server集成测试同上 | 同上，共2处修复 |

_记录数: 2 CRITICAL | 2 BUG | 创建: 2026-03-03_
