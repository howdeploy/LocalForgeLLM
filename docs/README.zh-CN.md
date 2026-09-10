# LocalForgeLLM 文档

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a> · <strong>简体中文</strong> · <a href="README.es.md">Español</a>
</p>

[返回项目](../README.zh-CN.md) · [安装](#安装) · [启动配置](#启动配置) · [实测数据](#rtx-4060-实测)

## 工作原理

1. 告诉编程智能体任务、目标上下文长度和内存预算。可以指定 MoE 模型，也可以让它选择。它会检查 CPU、GPU、内存、存储及已安装软件。
2. 根据框架、模型与运行时文档，选择兼容的引擎和权重格式。
3. 针对你的任务调整 CPU/GPU 分配、线程数、上下文、缓存精度和批次大小。
4. 运行任务、检查输出、测量速度及 RAM/VRAM 占用，并继续优化参数。最终得到包含引擎版本和参数的可复用启动配置。

![智能体根据任务和硬件选择并调优本地技术栈，测量结果，最终保存启动配置。](assets/how-it-works.svg)

下方的安装步骤与命令是**同一台电脑上的两个示例**：使用 APEX GGUF 的 Qwen 和 Gemma。框架对其他 MoE 模型和量化方法采用相同的选择与调优流程。

## 安装

**已验证的配置：** Linux x86_64、Vulkan 驱动、RTX 4060 8 GB、Ryzen 5 5600 和 32 GB 内存。Gemma 含视觉组件需预留约 22 GB SSD 空间，Qwen 约需 18 GB。这些是实测配置，并非适用于所有情况的最低要求。

1. 下载 [llama.cpp b10883 Vulkan 压缩包](https://github.com/ggml-org/llama.cpp/releases/download/b10883/llama-b10883-bin-ubuntu-vulkan-x64.tar.gz)，解压到 `runtime/`。
2. 创建 `models/`，下载下表中的一个配置。保留原始文件名；视觉投影器文件名为 `mmproj.gguf`。
3. 启动所选配置，然后打开 [localhost:8080](http://localhost:8080)。智能体客户端使用 `http://127.0.0.1:8080/v1`，模型 ID 为 `gemma-apex` 或 `qwen-apex`。每次运行一个模型。

| 配置 | 下载 |
|:--|:--|
| Gemma 4 26B-A4B Heretic · **I-Balanced** | [模型 · 19.51 GB](https://huggingface.co/mudler/gemma-4-26B-A4B-it-heretic-APEX-GGUF/resolve/8e3506b8b11a8ac2d666e0df473fa7ba4ec21497/gemma-4-26B-A4B-heretic-APEX-I-Balanced.gguf?download=true) + [视觉组件 · 1.19 GB](https://huggingface.co/mudler/gemma-4-26B-A4B-it-heretic-APEX-GGUF/resolve/8e3506b8b11a8ac2d666e0df473fa7ba4ec21497/mmproj.gguf?download=true) |
| Qwen3.6 35B-A3B · **I-Compact** | [模型 · 17.29 GB](https://huggingface.co/mudler/Qwen3.6-35B-A3B-APEX-GGUF/resolve/316efc983b0d8d41290ceb4ad31bd9a66b6c54e8/Qwen3.6-35B-A3B-APEX-I-Compact.gguf?download=true) · 纯文本配置 |

## 启动配置

在包含 `runtime/` 和 `models/` 的目录中执行。压缩包会生成 `runtime/llama-b10883/`。在我们的配置中，`Vulkan0` 对应 RTX 4060；如果设备顺序不同，请调整该值。

### Gemma

需要 systemd 用户会话。服务的 11 GiB 内存上限包含文件缓存；`mmap` 允许回收模型页面，之后再从 SSD 读取。这能限制驻留内存，但可能带来 I/O 停顿。该上限不会为其他应用预留内存，也不能保证避免 OOM。

```bash
mkdir -p logs
systemd-run --user --unit=gemma-apex --collect \
  --property=MemoryMax=11G --property=MemorySwapMax=0 \
  --property=OOMPolicy=kill --property=OOMScoreAdjust=1000 \
  --property=LimitCORE=0 --property=CPUQuota=600% \
  --property=Nice=5 --property=TimeoutStopSec=15 \
  --property="StandardOutput=append:$PWD/logs/gemma-server.log" \
  --property=StandardError=inherit \
  "$PWD/runtime/llama-b10883/llama-server" \
  --model "$PWD/models/gemma-4-26B-A4B-heretic-APEX-I-Balanced.gguf" \
  --mmproj "$PWD/models/mmproj.gguf" \
  --no-mmproj-offload --image-max-tokens 1120 \
  --alias gemma-apex --host 127.0.0.1 --port 8080 --cors-origins localhost \
  --device Vulkan0 --gpu-layers all --n-cpu-moe 27 --fit off \
  --load-mode mmap --threads 6 --threads-batch 6 \
  --ctx-size 32768 --parallel 1 --batch-size 1152 --ubatch-size 1152 \
  --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
  --cache-ram 0 --ctx-checkpoints 1 \
  --temp 1.0 --top-p 0.95 --top-k 64 --min-p 0 \
  --log-colors off --log-timestamps
```

使用 `systemctl --user stop gemma-apex` 停止服务。投影器在 CPU 上运行。图像 token 上限为 1120 时，请将两个批次大小都保留为 1152：在此版本中，较小的微批次会在处理图像时触发断言错误。

### Qwen

在前台运行，使用 `Ctrl+C` 停止。此配置没有服务内存上限，也不加载视觉投影器。

```bash
./runtime/llama-b10883/llama-server \
  --model ./models/Qwen3.6-35B-A3B-APEX-I-Compact.gguf \
  --alias qwen-apex --host 127.0.0.1 --port 8080 --cors-origins localhost \
  --device Vulkan0 --gpu-layers all --n-cpu-moe 36 --fit off \
  --load-mode none --threads 6 --threads-batch 6 \
  --ctx-size 32768 --parallel 1 --batch-size 512 --ubatch-size 128 \
  --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
  --cache-ram 0 --ctx-checkpoints 4 \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0 \
  --log-colors off --log-timestamps
```

## APEX 示例

这些配置使用 [APEX](https://github.com/localai-org/apex-quant) 混合精度 GGUF 权重。它根据张量职责和所在层分配精度；`I-` 配置使用重要性矩阵校准。MoE 每处理一个 token 只激活部分专家，llama.cpp 则在 CPU 与 GPU 之间分配计算。完整模型共同存放在 SSD、系统内存和显存中。

## RTX 4060 实测

Ryzen 5 5600 · 32 GB 内存 · Manjaro Linux · llama.cpp b10883 / Vulkan · 2026 年 9 月 10 日。

| 模型 / 配置 | 解码速度 | 上下文窗口 | 内存 / 模型显存 |
|:--|--:|--:|:--|
| Qwen3.6 35B-A3B · I-Compact | **21.11 token/s** | **32,768** | RSS 峰值 13.43 GiB / 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + 视觉 | **9.78 token/s** | **32,768** | 服务上限 11 GiB / 快照值 4.88 GiB |

Qwen：28 个已完成请求，19.37–22.09 token/s，报告的上下文最多为 29,087 token。Gemma：启用视觉功能后的一个已完成请求，输入 599 / 输出 632 token。配置 32K 窗口并不代表完成了满窗口压力测试；解码速度不包含提示词处理时间。

## 资源占用与测量方法

Qwen 的资源监控覆盖会话前 10 分 44 秒，共 314 个采样点，包含暂停时间：

| 资源 | 平均值 / 最大值 |
|:--|:--|
| 模型内存，RSS | 13.23 / 13.43 GiB |
| 模型显存 | 4.07 / 4.07 GiB |
| 模型 CPU 占用，按全部 12 个逻辑线程归一化 | 10.1% / 46.9% |
| 整块 GPU 利用率，包含桌面应用 | 89.8% / 100% |
| GPU 温度 | 50.4 / 54 °C |

系统可用内存最低为 2.53 GiB，空闲显存最低为 811 MiB。Gemma 达到了 11 GiB 的 cgroup 上限，该数值包含文件缓存，与 RSS 不是同一指标。其 4.88 GiB 显存是一次快照；此配置未记录 CPU/GPU 利用率。

Qwen 在 28 个已完成请求中生成了 7,820 token。按照 llama.cpp 对首个 token 的计时方式，按时间加权的解码速度为 `(7820 − 28) / 369.07315 = 21.11 token/s`。新输入的平均处理速度为 67.36 token/s。Gemma 的提示词处理耗时 97.59 秒，解码耗时 64.55 秒，总计 162.13 秒。这些测量反映服务速度，不是模型质量评测。

## Colibri 与 FreeToken 对比

![Qwen3.6 对比：LocalForgeLLM 为 21.11，Colibri 为 9.9，FreeToken 为 39.3 token/s。本地 RSS 峰值为 13.43 GiB；Colibri 报告 40 GB；FreeToken 列出 32 GiB 安装内存。硬件和量化方式不同。](assets/comparison.svg)

- **[Colibri](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md)：** 作者报告冷 / 热路由历史下为 9.2 / 9.9 token/s，RSS 峰值为 40 GB，硬件为 Threadripper 3945WX + RTX 3070 8 GB，int4，生成 200 token。
- **[FreeToken](https://arxiv.org/html/2608.16157v1#S5)：** 作者报告在 RTX 4060 Laptop 8 GB + i9-13900H、32 GiB LPDDR5 上达到 39.3 token/s，使用 NVFP4 和 OpenCode 编程任务。安装的内存容量不是进程内存占用的实测值。

我们的 Qwen 速度为上述 Colibri 热状态速度的 **2.13 倍**，比上述 FreeToken 速度**低 46.3%**。各行使用的 CPU、格式、任务和平均方式不同。我们与 Colibri 的内存数值是进程 RSS；FreeToken 的 32 GiB 是安装容量。Gemma 的 11 GiB 是包含文件缓存的服务上限。比较配置时请保留这些指标定义。
