# SKILL: tdd-cycle
# 适用：所有模式（L/M/H），含可直接复制的代码模板
# 核心：RED→GREEN→REFACTOR + 已知坑预防

---

## 标准流程

### RED（先写测试，先跑失败）
1. 按 BRIEF/SPEC 写测试
2. **运行，确认 FAIL**（若直接 PASS，说明测试写错了，重写）
3. 记录失败的断言行

### GREEN（最小实现）
1. 只写让测试通过的最少代码
2. 不提前优化
3. 运行，确认 PASS

### REFACTOR（保持 GREEN 重构）
1. 消除重复，改善命名
2. 运行，确认仍 PASS

---

## ★ 模板库（直接复制，按需修改）

### TCP 服务端 recv 循环（★ MEM_F_C_004）

```python
def handle_client(conn: socket.socket) -> None:
    """
    ★ MEM_F_C_004: recv 循环外层必须精确捕获三类异常
    TCP 服务器 close 后对端收到 ECONNRESET，Python 表现为 ConnectionResetError
    只用 except Exception 会掩盖真实错误语义，高并发下有静默风险
    """
    buf = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break          # 对端正常关闭
            buf += data
            # —— 在此处理 buf，调用 parse + execute ——
    except (socket.timeout, ConnectionResetError, OSError):
        pass   # 正常：连接重置 / 超时 / socket 已关闭
    except Exception:
        pass   # 非预期异常（可加日志）
    finally:
        conn.close()  # 必须在 finally，保证总是执行
```

### recv_all 测试 helper（★ MEM_F_C_004）

```python
def recv_all(sock: socket.socket, timeout: float = 1.0) -> bytes:
    """
    ★ MEM_F_C_004: 测试 helper 同样需要精确捕获
    服务器发完响应后立刻 close，会触发 ConnectionResetError
    """
    sock.settimeout(timeout)
    buf = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
    except (socket.timeout, ConnectionResetError, OSError):
        pass
    return buf
```

### socketpair 单元测试（★ MEM_F_I_001）

```python
import socket, threading, unittest

class TestHandleClient(unittest.TestCase):
    def _run_handler(self, handler_fn, send_data: bytes) -> bytes:
        """用 socketpair 在进程内测试，无需真实网络"""
        srv_sock, cli_sock = socket.socketpair()
        t = threading.Thread(target=handler_fn, args=(srv_sock,), daemon=True)
        t.start()
        cli_sock.sendall(send_data)
        response = recv_all(cli_sock)  # 使用上面的 recv_all
        cli_sock.close()
        t.join(timeout=2)
        return response

    def test_ping(self):
        resp = self._run_handler(handle_client, b"*1\r\n$4\r\nPING\r\n")
        self.assertIn(b"+PONG", resp)
```

### 线程安全存储（使用 RLock）

```python
import threading

class Store:
    """
    使用 RLock（递归锁）而非 Lock：
    若同一线程在锁内调用其他需要锁的方法，Lock 会死锁，RLock 不会
    """
    def __init__(self):
        self._data: dict = {}
        self._lock = threading.RLock()   # ← RLock，不是 Lock

    def get(self, key: str):
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = value
```

---

## 卡住处理（RED 超过 2 次）

1. 停止修改代码
2. 运行 `@hooks/stuck-detector/HOOK.md` 或手动调用 `@skills/diagnose-bug/SKILL.md`
3. **禁止改测试断言**（MEM_F_C_003）
4. 若确认测试本身有 bug：先记录原因再修改，重新走 RED→GREEN
