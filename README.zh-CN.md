# LocalForgeLLM

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a> · <strong>简体中文</strong> · <a href="README.es.md">Español</a>
</p>

**用现有硬件运行更大的模型。** LocalForgeLLM 是一个让编程智能体构建并优化本地 AI 技术栈的框架。你提供任务，也可以指定 MoE 模型；智能体为你的硬件匹配模型、推理引擎、量化方案和启动参数。搭建好的技术栈可用于本地聊天、视觉和编程智能体。

**技术栈：** AI 编程智能体 · 模型与引擎文档 · Python / Bash · [llama.cpp](https://github.com/ggml-org/llama.cpp) 等推理引擎 · CPU / GPU 后端 · 本地 HTTP API。

## 安装

**所需条件：** 能访问终端的编程智能体，以及存放所选模型的空间。智能体会根据你的电脑选择依赖项和内存设置。

1. 在编程智能体中打开本仓库，让它阅读 [AGENTS.md](AGENTS.md) 和 [SKILL.md](SKILL.md)。
2. 描述任务、所需上下文长度和 RAM/VRAM 预算。可以指定模型，也可以交给智能体选择。
3. 让智能体按照框架文档安装引擎、调优模型，并保存可用的启动配置。

需要具体的起点时，可参考我们的 [Qwen 和 Gemma 启动示例](docs/README.zh-CN.md#安装)。

## 工作原理

智能体分析硬件和模型文档，选择合适的模型、兼容的引擎与权重格式，再调整 CPU/GPU 分配、上下文、缓存和批次大小。它运行你的任务，测量速度与内存占用，调整参数，并保存效果最好的可用配置。同一个流程适用于不同 MoE 系列和量化方法。

![智能体根据任务和硬件选择引擎、调优模型、测量结果并迭代参数，最终保存可复用的本地启动配置。](docs/assets/how-it-works.svg)

## RTX 4060 示例

Ryzen 5 5600 · 32 GB 内存 · 8 GB 显存 · 32K 上下文 · 2026 年 9 月 10 日。这两个配置采用 **APEX GGUF + llama.cpp / Vulkan**。

| 模型 / 配置 | 解码速度 | 内存 | 模型显存 |
|:--|--:|:--|--:|
| Qwen3.6 35B-A3B · I-Compact | **21.11 token/s** | RSS 峰值 13.43 GiB | 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + 视觉 | **9.78 token/s** | 服务上限 11 GiB | 快照值 4.88 GiB |

Qwen：28 个请求，上下文最多为 29,087 token。Gemma：启用视觉功能后的一个请求。表中速度为 token 生成速度。

![Qwen3.6 对比：LocalForgeLLM 为 21.11，Colibri 为 9.9，FreeToken 为 39.3 token/s。本地 RSS 峰值为 13.43 GiB；Colibri 报告 40 GB；FreeToken 列出 32 GiB 安装内存。测试条件不同。](docs/assets/comparison.svg)

在上图所列配置下，我们的 Qwen 速度为 [Colibri 报告的热状态速度](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md)的 **2.13 倍**，比 [FreeToken 报告的速度](https://arxiv.org/html/2608.16157v1#S5)**低 46.3%**。35B 模型在此配置下运行时，**进程 RSS 峰值为 13.43 GiB，模型显存占用为 4.07 GiB**。[配置、指标定义与来源 →](docs/README.zh-CN.md#colibri-与-freetoken-对比)

## 文档

[智能体技能](SKILL.md) · [框架操作指南](docs/README.zh-CN.md#智能体操作指南) · [简体中文文档](docs/README.zh-CN.md) · [启动配置](docs/README.zh-CN.md#启动配置) · [测量方法](docs/README.zh-CN.md#资源占用与测量方法) · [详细对比](docs/README.zh-CN.md#colibri-与-freetoken-对比)
