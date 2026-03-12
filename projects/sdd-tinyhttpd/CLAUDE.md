# 项目：sdd-tinyhttpd
# 创建日期：2026-03-03
# 框架版本：v3.0
# 框架根：../../

---

## Step 0：AI 启动协议

读取本文件后输出：
`"[已就绪] 项目: sdd-tinyhttpd | 强制规则: 5 条已加载 | 模式: M标准"`

---

## Step 1：复杂度评估结果

```
总分: 6/12
等级: M 标准模式
关键因素: 网络/TCP(2分) + 外部协议HTTP/1.0(2分) + 3-5模块(1分)
```

---

## ⚡ 强制规则（5 条，每次写代码前确认）

1. **先写 SPEC 再写代码**，绝不先实现
2. **SPEC 必须明确接口 dtype**（bytes/str 不能模糊，见各模块 SPEC 输出规格）
3. **测试失败只改实现**，禁止改断言或 skip
4. **recv() 必须用** `except (socket.timeout, ConnectionResetError, OSError)`，禁止 `except Exception`
5. **socket 发送必须是 bytes**；recv 返回 `b''` 表示连接关闭，必须 `if not data: break`

---

## 强制检查点

| 时机 | 执行命令 |
|------|---------|
| 写完任何网络代码后 | `bash ../../framework/hooks/pre-commit-check.sh ./modules/<模块名>/` |
| 所有测试 PASS 后 | `bash ../../framework/hooks/post-green.sh ./` |

---

## 模式：M 标准

文档结构：CONTEXT.md + 每模块 SPEC.md  
实现顺序：M01(response) → M02(request_parser) → M03(router) → M04(static_handler) → M05(cgi_handler) → M06(server)  
检查：每模块完成即 TDD，网络模块完成即 pre-commit-check.sh

---

## 运行环境

```bash
# 有 pytest
python3 -m pytest modules/ -v

# 无 pytest（标准库）
python3 -m unittest discover -s modules -p "test_*.py" -v

# 检查脚本
bash ../../framework/hooks/pre-commit-check.sh ./modules/server/
bash ../../framework/hooks/post-green.sh ./
```

---

## 项目特有约束

- 工作目录必须是含 `htdocs/` 的目录（server 使用相对路径）
- 测试时需 `os.chdir` 到含 `htdocs/` 的临时目录
- CGI 脚本须预检可执行性再发 200（见 modules/cgi_handler/SPEC.md）
- POST body 读取：`parse_content_length` 后必须再调 `drain_headers`（见 modules/server/SPEC.md）
