# Memory 索引（INDEX.md）
# ⚠️ Agent 必读 | 保持 <80 行 | 只记路，不记内容

## ⚡ CRITICAL（每次 Agent 启动必加载）
| ID | 标题 | 路径 |
|----|------|------|
| MEM_F_C_001 | 校验器必须先自测 | [→](framework/critical/MEM_F_C_001.md) |
| MEM_F_C_002 | SPEC 必须包含 dtype | [→](framework/critical/MEM_F_C_002.md) |
| MEM_F_C_003 | 禁止修改测试用例 | [→](framework/critical/MEM_F_C_003.md) |
| MEM_F_C_004 | socket数据全程bytes | [→](framework/critical/MEM_F_C_004.md) |
| MEM_F_C_005 | recv空bytes=连接关闭 | [→](framework/critical/MEM_F_C_005.md) |

## 📋 IMPORTANT（按任务类型加载）
| 任务类型 | 加载路径 | 条数 |
|---------|---------|------|
| c_to_python | framework/important/ | 2 |
| http_server | domains/http_networking/ | 3 |
| tdd_impl | framework/important/ | 4 |

## 🔭 领域记忆（按项目领域加载）
| 领域 | 索引 | 条数 |
|------|------|------|
| http_networking | [→](domains/http_networking/INDEX.md) | 3 |

## 🏗️ 项目记忆（按当前项目加载）
| 项目 | 索引 |
|------|------|
| tinyhttpd | [→](projects/tinyhttpd/INDEX.md) |

_记录总数: 5 CRITICAL + 6 IMPORTANT | 下次淘汰检查: 2026-09-03_

## 新增（2026-03-03 tinyhttpd验证）
| MEM_F_C_004 | socket测试recv_all必须捕获ConnectionResetError | [→](framework/critical/MEM_F_C_004.md) |
