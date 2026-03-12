# 项目 Memory 索引 — sdd-tinyhttpd
# 只记"此项目特有、换个项目就不适用"的经验
# 通用经验已写入 ../../framework/memory/

## 项目特有 Bug 修复经验

| ID | 发现于 | 根因摘要 | 文件 |
|----|--------|---------|------|
| P_THD_001 | cgi_handler 实现 | CGI 先发 200 后检查可执行性导致头部混乱 | P_THD_001.md |
| P_THD_002 | server E2E | POST body 读取偏移：parse_content_length 不消费空行 | P_THD_003.md |

## 项目特有设计决策

| ID | 决策 | 原因 |
|----|------|------|
| D_THD_001 | 工作目录必须含 htdocs/ | C 原版使用相对路径，Python 版保持行为等价 |
| D_THD_002 | CGI 用 Popen 不用 fork | Python 多线程环境 fork 危险（锁状态） |

_记录数: 2 Bug + 2 决策 | 最后更新: 2026-03-05_
