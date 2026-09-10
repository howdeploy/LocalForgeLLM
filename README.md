# LocalForgeLLM

<p align="center">
  <strong>English</strong> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a>
</p>

**Bigger models on the hardware you have.** LocalForgeLLM is a framework that lets your coding agent build and tune a local AI stack. Give it a task and, optionally, a MoE model; the agent matches the model, runtime, quantization and launch settings to your hardware. Use the result for local chat, vision and coding agents.

**Stack:** AI coding agents · model and runtime documentation · Python / Bash · inference engines such as [llama.cpp](https://github.com/ggml-org/llama.cpp) · CPU / GPU backends · local HTTP API.

## Install

**You need:** a coding agent with terminal access and space for the chosen model. The agent selects dependencies and memory settings for your machine.

1. Open this repository in your coding agent.
2. Describe the task, desired context size and RAM/VRAM budget. Specify a model or let the agent choose one.
3. Ask it to use the framework documentation to set up the runtime, tune the model and save a working launch profile.

For a concrete starting point, use our [Qwen and Gemma launch examples](docs/README.md#install).

## How it works

The agent inspects your hardware and model documentation, selects a suitable model, engine and weight format, then tunes CPU/GPU placement, context, cache and batching. It runs your workload, measures speed and memory use, adjusts the settings and saves the best working profile. The same workflow applies to different MoE families and quantization methods.

![Your task and hardware guide an agent through runtime selection, model tuning, measurement and refinement, ending in a reusable local launch profile.](docs/assets/how-it-works.svg)

## Examples on an RTX 4060

Ryzen 5 5600 · 32 GB RAM · 8 GB VRAM · 32K context · September 10, 2026. These two profiles use **APEX GGUF + llama.cpp / Vulkan**.

| Model / profile | Decode | RAM | Model VRAM |
|:--|--:|:--|--:|
| Qwen3.6 35B-A3B · I-Compact | **21.11 tok/s** | 13.43 GiB peak RSS | 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + vision | **9.78 tok/s** | 11 GiB service limit | 4.88 GiB snapshot |

Qwen: 28 requests, up to 29,087 context tokens. Gemma: one request with vision enabled. Rates show token generation.

![Qwen3.6 comparison: LocalForgeLLM 21.11, Colibri 9.9, FreeToken 39.3 tokens per second. Local peak RSS is 13.43 GiB; Colibri reports 40 GB; FreeToken lists 32 GiB installed RAM. Different test setups.](docs/assets/comparison.svg)

Our Qwen rate is **2.13×** [Colibri's reported warm rate](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md) and **46.3% below** [FreeToken's reported rate](https://arxiv.org/html/2608.16157v1#S5), across the configurations shown above. A 35B model runs here with **13.43 GiB peak RSS and 4.07 GiB model VRAM**. [Settings, measurement definitions and sources →](docs/README.md#comparison-with-colibri-and-freetoken)

## Documentation

[English documentation](docs/README.md) · [Launch profiles](docs/README.md#launch-profiles) · [Measurement methodology](docs/README.md#resource-use-and-methodology) · [Comparison details](docs/README.md#comparison-with-colibri-and-freetoken)
