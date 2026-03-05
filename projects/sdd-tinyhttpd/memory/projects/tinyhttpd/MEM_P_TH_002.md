---
id: MEM_P_TH_002
title: 跨语言重构项目的fixture策略：语义基准代替执行基准
tags:
  domain: http_server
  task_type: spec_writing
  severity: CRITICAL
created: 2026-03-03
expires: never
confidence: high
---

## 经验
SDD框架原设计假设参考项目与重构项目语言相同（可运行生成pkl fixture）。
C→Python跨语言重构时，无法运行C代码生成fixture，需调整策略。

## 正确策略：语义基准
不依赖"运行参考项目得到输出"，而是从源码分析提取语义约定：
1. 从C源码注释和行为分析，手写期望的输出bytes
2. 用HTTP协议规范作为基准（RFC），而非C代码输出
3. 测试验证"语义正确"而非"与C输出bit-for-bit一致"

## 对SDD框架的改进建议
在generate_reference.py中增加"语义基准"模式，允许手写期望值而非运行参考项目。
在HOW_TO_START_PROJECT.md中增加"跨语言重构"路径说明。
