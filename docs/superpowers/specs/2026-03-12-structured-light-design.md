# 多线结构光立体视觉 DEMO · 设计规格文档
> 日期: 2026-03-12 | 复杂度: 8/10 | 工作模式: H（完整）
> 项目路径: projects/sdd-structured-light

---

## 1. 项目背景与目标

基于 Python 实现多线结构光立体视觉工程验证 DEMO。使用海康威视工业 RGB 相机（MVS SDK）配合 IO 控制的多线蓝色激光器，通过分时触发采集多组激光线图像，经亚像素级线条提取与激光平面三角化，实时重建物体表面三维点云并可视化显示。

**核心目标：** 端到端跑通完整采集→处理→可视化流水线，验证工程可行性。

---

## 2. 硬件配置

| 组件 | 规格 |
|------|------|
| 相机 | 海康威视工业 RGB 相机，MVS SDK（MvCameraControl Python 绑定） |
| 激光器 | 多线蓝色激光器（~450nm），多组线，每组独立 IO 触发 |
| 触发方式 | 分时触发：每次 IO 触发一组线，采集对应帧，循环遍历所有组 |
| 图像格式 | BGR uint8，(H, W, 3) |

---

## 3. 架构：生产者-消费者双线程

```
┌─────────────────────────────────────────────────────────┐
│                      pipeline                           │
│                                                         │
│  ┌──────────────┐   frame_q    ┌──────────────────────┐ │
│  │ 采集线程      │ ──────────► │ 处理线程              │ │
│  │ AcquireThread│  Queue(8)   │ ProcessThread         │ │
│  │              │             │                       │ │
│  │ for line_id  │             │ line_extractor        │ │
│  │  IO触发激光  │             │ triangulator          │ │
│  │  MVS采集帧   │             │ 组装 line_id→points   │ │
│  │  put(frame,  │             │ 当所有线收齐→         │ │
│  │    line_id)  │             │ put(points) →result_q │ │
│  └──────────────┘             └──────────────────────┘ │
│                                      result_q           │
│                               ──────────────────────►  │
│                                 Queue(4)   主线程/渲染  │
└─────────────────────────────────────────────────────────┘
```

**队列策略：**
- `frame_q` 满时丢帧（`put(block=False)`），保持实时性
- 线程停止信号：哨兵值 `None` 入队
- 多线拼合：处理线程内部 `dict[line_id → points]` 收齐后合并
- 异常隔离：每线程独立 `try/except`，错误写入 `error_q`
- 无共享状态，纯队列通信，无需 Lock

---

## 4. 模块划分

```
sdd-structured-light/
├── modules/
│   ├── camera/          # 海康 MVS 采集 + IO 触发
│   ├── line_extractor/  # 颜色增强 + 高斯拟合亚像素线条提取
│   ├── triangulator/    # 激光平面三角化 → 3D 点
│   ├── calibration/     # 离线标定工具（棋盘格 + 平面拟合）
│   ├── visualizer/      # OpenCV 实时深度图 + Open3D 点云窗口
│   └── pipeline/        # 生产者-消费者协调，队列管理
├── calib/
│   ├── camera_params.npz    # camera_matrix, dist_coeffs
│   ├── laser_planes.npz     # planes: float32 (N_lines, 4)
│   └── calib_report.txt     # 重投影误差记录
└── scripts/
    ├── run_calib.py     # 标定脚本（离线运行）
    └── run_demo.py      # 主入口（启动 pipeline）
```

---

## 5. 接口规格（dtype 精确）

| 模块 | 输入 | 输出 |
|------|------|------|
| `camera` | `line_id: int` | `np.ndarray` uint8 (H, W, 3) BGR |
| `line_extractor` | `np.ndarray` uint8 (H, W, 3) BGR | `np.ndarray` float32 (N, 2) 亚像素坐标 |
| `triangulator` | `uv: float32 (N,2)`, `plane: float32 (4,)` | `np.ndarray` float32 (N, 3) XYZ |
| `calibration` | 图像路径列表 | `camera_params.npz`, `laser_planes.npz` |
| `visualizer` | `np.ndarray` float32 (N, 3) | 无（直接渲染） |
| `pipeline` | 配置 `dict` | 无（协调所有模块运行） |

### line_extractor 颜色增强策略

蓝色激光（~450nm），BGR 格式：
```python
# B - (R+G)/2，强调蓝色激光，压制环境光
enhanced = B.astype(int16) - (R.astype(int16) + G.astype(int16)) // 2
enhanced = clip(enhanced, 0, 255).astype(uint8)
```
颜色模式通过配置参数暴露：`color_mode: "B-RG" | "B-R" | "single_B"`，默认 `"B-RG"`。

### triangulator 三角化算法

```
输入: uv float32(N,2), plane float32(4,) = [a,b,c,d], K_inv float32(3,3)
算法: 射线与平面求交
  ray = K_inv @ [u, v, 1]ᵀ
  t   = -d / (a·ray[0] + b·ray[1] + c·ray[2])
  XYZ = t · ray
输出: float32(N,3)
```

---

## 6. 标定流程（离线，两步走）

### 步骤 1：相机内参标定
- 输入：20~30 张不同角度棋盘格图像
- 工具：`cv2.calibrateCamera`
- 输出：`calib/camera_params.npz`（`camera_matrix`, `dist_coeffs`）

### 步骤 2：激光平面标定（每条线单独标定）
```
① 检测棋盘格角点 → 计算棋盘格平面在相机坐标系的位姿
② 提取该帧激光线亚像素坐标（使用 line_extractor）
③ 将激光点反投影到棋盘格平面 → 得到 3D 点
④ 对多帧 3D 点做平面拟合（SVD） → 激光平面方程 ax+by+cz+d=0
```
- 输出：`calib/laser_planes.npz`（`planes: float32 (N_lines, 4)`）

---

## 7. 分时触发节拍（以 3 条线为例）

```
t0: IO触发 line_0 → 采集帧0 → frame_q
t1: IO触发 line_1 → 采集帧1 → frame_q
t2: IO触发 line_2 → 采集帧2 → frame_q

处理线程：
  帧0 → line_extractor → p0 → dict[0]=p0
  帧1 → line_extractor → p1 → dict[1]=p1
  帧2 → line_extractor → p2 → dict[2]=p2
  收齐 N_lines → concat → result_q → 渲染一帧点云
```

---

## 8. 技术栈

| 用途 | 库 |
|------|-----|
| 相机采集 | `MvCameraControl`（海康 MVS SDK Python 绑定） |
| 图像处理 | `opencv-python`，`numpy` |
| 标定 | `opencv-python`（cv2.calibrateCamera, cv2.findChessboardCorners） |
| 三角化 | `numpy`（纯向量运算） |
| 点云可视化 | `open3d` |
| 测试 | `pytest` |

---

## 9. 测试策略

| 层级 | 测试对象 | Mock 策略 | 断言目标 |
|------|---------|----------|---------|
| 单元 | `line_extractor` | 合成蓝色激光图像（已知线位置） | 亚像素误差 < 0.1px |
| 单元 | `triangulator` | 硬编码平面 + 已知 UV | XYZ 误差 < 0.1mm |
| 单元 | `calibration` | 合成棋盘格点 | 重投影误差 < 0.5px |
| 集成 | `pipeline` | MockCamera（返回预录帧） | 队列流通、线程干净退出 |
| E2E | 全流程 | 真实相机（手动执行） | 目视点云合理，无崩溃 |

### 合成测试图像（line_extractor 单元测试核心）

```python
def make_test_image(height=480, width=640, line_y=120.3, sigma=1.5):
    """在已知位置生成蓝色高斯亮线，验证提取精度"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    ys = np.arange(height)
    profile = np.exp(-0.5 * ((ys - line_y) / sigma) ** 2) * 200
    img[:, :, 0] = profile[:, None]  # B 通道（BGR，蓝色激光）
    return img
# 断言：提取到的 y 均值与 line_y 偏差 < 0.1
```

---

## 10. 验收标准

```
功能验收：
  [ ] run_calib.py 完成双步标定，calib_report.txt 重投影误差 < 0.5px
  [ ] run_demo.py 启动后实时窗口显示点云，无卡顿（> 5 fps）
  [ ] 分时触发 N 条线，每轮完整收齐后渲染一帧
  [ ] Ctrl+C 干净退出，无线程泄漏

测试验收：
  [ ] pytest 全绿（0 SKIP 0 ERROR）
  [ ] line_extractor 亚像素误差 < 0.1px（合成图像）
  [ ] triangulator XYZ 误差 < 0.1mm（已知平面）
  [ ] pipeline 集成测试：1000 帧 MockCamera 无队列溢出、无死锁
```

---

## 11. 框架分流

- 复杂度：**8/10 → H 模式**
- 文档要求：完整文档 + 各模块 SPEC.md + Agent 流水线
- 记忆加载：CRITICAL 内联 + 按需领域记忆
