# 全局任务追踪（TODO.md）— tinyhttpd

## 阶段 0-3：初始化+规划 ✅
- [x] 框架目录结构
- [x] reference_project/httpd.c
- [x] CONTEXT.md §1-5
- [x] memory/INDEX.md + CRITICAL记录(5条)
- [x] memory/domains/http_networking/ (3条IMPORTANT)
- [x] 所有模块 SPEC.md (M01-M06)
- [x] PLAN.md

## 阶段 4：Fixtures + 校验器 ✅
- [x] M01 response: fixtures生成
- [x] M01 response: validator创建+自测 ✅
- [x] M02 request_parser: fixtures生成（MockSocket方案）
- [x] M03 router: fixtures生成
- [x] M04 static_handler: fixtures生成
- [x] M05 cgi_handler: fixtures生成

## 阶段 5：TDD 实现 ✅
- [x] M01 response: RED→GREEN→VALIDATE (14测试)
- [x] M02 request_parser: RED→GREEN (16测试)
- [x] M03 router: RED→GREEN (14测试)
- [x] M04 static_handler: RED→GREEN (6测试)
- [x] M05 cgi_handler: RED→GREEN (7测试) — 发现并修复CGI错误响应Bug
- [x] M06 server: 集成实现+端到端测试 (6测试)
- [x] 全量测试: 63/63 PASS

## 阶段 6：集成测试 ✅
- [x] htdocs/ 创建（index.html + hello.cgi）
- [x] run_all_validators.py: 1/1 PASS (response)
- [x] 端到端：GET静态文件 → 200+内容
- [x] 端到端：GET不存在 → 404
- [x] 端到端：GET CGI?query → 200+CGI输出

## 阶段 7：经验沉淀 ✅
- [x] MEM_F_C_004: socket全程bytes（CRITICAL）
- [x] MEM_F_C_005: recv空bytes=连接关闭（CRITICAL）
- [x] MEM_D_HTTP_001: HTTP响应必须\r\n
- [x] MEM_D_HTTP_002: CGI用subprocess不用fork
- [x] MEM_D_HTTP_003: C fd→Python socket对象转换
- [x] MEM_P_TINYHTTPD_001: CGI须预检可执行性（项目Bug经验）
- [x] MEM_F_I_001: 测试须捕获ConnectionResetError（框架经验）
- [x] MEM_F_I_002: C→Python重构通用模式（框架经验）

## 🚨 阻塞项
_(无)_
