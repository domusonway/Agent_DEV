# HOOK: network-guard
# 触发：写任何包含 socket / recv / send / connect 的代码后立即执行
# 目的：在代码提交前强制检查 MEM_F_C_004，不依赖事后测试发现

## 检查项（逐条过）

```
□ 1. recv 循环的 except 是否精确？
      ✅ except (socket.timeout, ConnectionResetError, OSError):
      ❌ except Exception:  ← 最常见违规
      ❌ bare except:       ← 同样违规

□ 2. handle_client 是否有 try/finally 保证 conn.close()？
      ✅ finally: conn.close()
      ❌ close() 只在正常路径

□ 3. socket.send/sendall 的参数是 bytes 吗？（MEM_F_C_002）
      ✅ conn.sendall(b"+OK\r\n")
      ✅ conn.sendall(response.encode())
      ❌ conn.sendall("+OK\r\n")  ← str 直接发

□ 4. 服务端 socket 是否设置了 SO_REUSEADDR？
      ✅ srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      ❌ 无此行 → 测试结束后端口占用导致下次 bind() 失败

□ 5. 测试中的 recv_all helper 是否也用了精确捕获？
      测试 helper 同样需要 except (socket.timeout, ConnectionResetError, OSError)
```

## 自动检查脚本

```python
# 保存为 check_network.py，在写完网络代码后运行
import sys, re

def check(filepath):
    src = open(filepath).read()
    issues = []

    if 'recv(' in src:
        # 检查精确捕获
        if 'ConnectionResetError' not in src:
            issues.append(
                f"❌ MEM_F_C_004: {filepath} 有 recv() 但缺少 ConnectionResetError 捕获\n"
                f"   修复: except (socket.timeout, ConnectionResetError, OSError):"
            )
        if 'finally' not in src and 'conn.close()' in src:
            issues.append(f"⚠️  {filepath}: conn.close() 不在 finally 块中")

    if 'sendall(' in src or 'send(' in src:
        # 粗略检查是否有 str 直接传给 send（启发式）
        lines = src.splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r'send(?:all)?\s*\(\s*["\']', line):
                issues.append(
                    f"❌ MEM_F_C_002: {filepath}:{i} 可能在发 str 而非 bytes\n"
                    f"   {line.strip()}"
                )

    return issues

if __name__ == '__main__':
    all_issues = []
    for f in sys.argv[1:]:
        all_issues.extend(check(f))
    if all_issues:
        print('\n'.join(all_issues))
        sys.exit(1)
    else:
        print("✅ network-guard 通过")
```

使用方式：
```bash
python3 check_network.py server/__init__.py
```

## 违规处理

1. **立即停止**，不继续写其他代码
2. 按检查项修复
3. 重新运行此 hook，全部通过后继续
