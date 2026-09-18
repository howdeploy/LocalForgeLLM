# LocalForgeLLM

<p align="center">
  <strong>English</strong> · <a href="README.ru.md">Русский</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.es.md">Español</a>
</p>

**Bigger models on the hardware you have.** LocalForgeLLM is a framework that lets your coding agent build and tune a local AI stack. Give it a task and, optionally, a dense or MoE model; the agent matches the model, runtime, quantization and launch settings to your hardware. Use the result for local chat, vision and coding agents.

**Stack:** AI coding agents · llama.cpp / PrismML kernels · CPU / GPU placement · APEX mixed precision · REAP expert pruning · native MTP · optional MCP / Jev API tools.

## Install

**You need:** a coding agent with terminal access and space for the chosen model. The agent selects dependencies and memory settings for your machine.

1. Open this repository in your coding agent and have it read [AGENTS.md](AGENTS.md) and [SKILL.md](SKILL.md).
2. Describe the task, desired context size and RAM/VRAM budget. Specify a model or let the agent choose one.
3. Ask it to use the framework documentation to set up the runtime, tune the model and save a working launch profile.

For a concrete starting point, use our [Qwen and Gemma launch examples](docs/README.md#install).

## How it works

The agent inspects your hardware and model documentation, selects a suitable model, engine and weight format, then tunes CPU/GPU placement, context, cache and batching. It runs your workload, measures speed and memory use, adjusts the settings and saves the best working profile. For derived weights, it composes conversion, pruning, calibration and quantization with separate quality checks.

![Your task and hardware guide an agent through runtime selection, model tuning, measurement and refinement, ending in a reusable local launch profile.](docs/assets/how-it-works.svg)

## Bonsai 2: 27B on 8 GB, 59.65 tok/s on 12 GB

**September 18 update:** our **RTX 4060 8 GB / Ryzen 5 5600 / 32 GB RAM** runs Ternary Bonsai 2 27B **PTQ1_0** with 32K context, GPU Q4 KV and CPU vision. The final short-response check reached **27.14 tok/s**, versus 6.73 with CPU cache. A **31,018-token input** lookup decoded at **20.22 tok/s**. The model process used **6.24 GiB VRAM** in the recorded snapshot; desktop headroom remained tight.

A later [llama UI session with MCP](docs/benchmarks/bonsai.md#interactive-llama-ui-session-32k-on-rtx-4060) averaged **19.58 tok/s** across nine completed generations and **7,355 output tokens**, with one cancelled stream excluded. Its prompts included 10.8K–18.0K tokens of conversation and tool context; this is separate from the short-response check.

Community contributor **ap3x0s** tested an **RTX 5070 12 GB / i7-10700K / 32 GB RAM**: Bonsai **PQ2_0 + GPU Q8 KV + PrismML kernels** reached **59.65 tok/s** over 10K output tokens, **5.60×** the same report's Opus-Distill-v2 row. That run spent its output budget thinking before producing code; this is throughput evidence, not a coding-quality win.

![Bonsai: community RTX 5070 throughput and a separate RTX 4060 GPU-cache tuning result, with hardware and measurement limits.](docs/assets/bonsai.svg)

PTQ1_0 is **5.95 GB**, PQ2_0 is **7.21 GB**, and the optional Q8 vision module adds **0.63 GB**. Native ternary kernels and cache residency explain the tuning direction; the cross-model gap changes several factors together. The RTX 5070 result is not a prediction for an 8 GB card.

[Measurements and report credit](docs/benchmarks/bonsai.md) · [Numeric data](docs/benchmarks/bonsai.csv) · [Download, calibration and 32K launch recipe](docs/implementations/bonsai.md)

## Examples on an RTX 4060

Ryzen 5 5600 · 32 GB RAM · 8 GB VRAM · 32K context · September 10, 2026. These two profiles use **APEX GGUF + llama.cpp / Vulkan**.

| Model / profile | Decode | RAM | Model VRAM |
|:--|--:|:--|--:|
| Qwen3.6 35B-A3B · I-Compact | **21.11 tok/s** | 13.43 GiB peak RSS | 4.07 GiB |
| Gemma 4 26B-A4B Heretic · I-Balanced + vision | **9.78 tok/s** | 11 GiB service limit | 4.88 GiB snapshot |

Qwen: 28 requests, up to 29,087 context tokens. Gemma: one request with vision enabled. Rates show token generation.

![Qwen3.6 comparison: LocalForgeLLM 21.11, Colibri 9.9, FreeToken 39.3 tokens per second. Local peak RSS is 13.43 GiB; Colibri reports 40 GB; FreeToken lists 32 GiB installed RAM. Different test setups.](docs/assets/comparison.svg)

Our Qwen rate is **2.13×** [Colibri's reported warm rate](https://github.com/JustVugg/colibri/blob/main/docs/qwen36-cuda-tier.md) and **46.3% below** [FreeToken's reported rate](https://arxiv.org/html/2608.16157v1#S5), across the configurations shown above. A 35B model runs here with **13.43 GiB peak RSS and 4.07 GiB model VRAM**. [Settings, measurement definitions and sources →](docs/README.md#comparison-with-colibri-and-freetoken)

## Gemma 4 with MTP

**September 11 update:** the same RTX 4060 / Ryzen 5 5600 stack measured **14.83 tok/s** across two user requests with MTP. The longer response logged **1535 output tokens over 102.05 seconds of decode: 15.03 tok/s**. The target remains **Heretic APEX I-Balanced**; **Q8_0 is the separate MTP head**. Main CPU/GPU placement and the configured 32K context were retained.

![Gemma 4 deployment comparison: our APEX plus MTP stack, QAT CUDA and Vulkan on another 8 GB GPU, full Q8 on GB10, and a FreeToken report on a 16 GB GPU. Each row names its weights, hardware and evidence scope.](docs/assets/gemma4-comparison.svg)

![Gemma MTP observations: the initial Vulkan sessions, later CUDA comparison and separately attributed community controls.](docs/assets/gemma4-mtp.svg)

The preceding no-MTP request measured **9.81 tok/s**. The **+51.1% observed difference is not a controlled MTP gain**: prompts and output lengths differed. Maximum observed live context was 2265 tokens; formal quality and full-window tests remain pending. The separate head added 425.34 MiB of logged GPU weights and 211.10 MiB of GPU compute allocations; these are not whole-process peak measurements.

[Comparison, resource accounting and sources](docs/benchmarks/gemma4-mtp.md) · [Numeric timing data](docs/benchmarks/gemma4-mtp.csv) · [Agent workflow: download a matching head, enable, disable and diagnose MTP](docs/implementations/mtp.md)

## CUDA, MTP and RAM adaptation

The later September 11 sessions reached **18.80 tok/s weighted decode** across four responses with CUDA, MTP and a 20 GiB service cap; the fastest completed response measured **19.38 tok/s**. The infographic tracks 19 responses across eight phases. These are observed session differences: changing requests and cache state prevents isolating a CUDA-only gain.

![Gemma 4 adaptation across Vulkan, CUDA, MTP and RAM-cap changes, with observed decode rates and runtime build costs.](docs/assets/gemma4-cuda-mtp-ram.png)

The initial CUDA compilation took **10 min 30.161 s** with four workers and 2.1 GiB peak build memory. Downloads, configuration and validation took additional time that was not fully recorded. The runtime was rebuilt; the existing GGUF weights were reused.

[Phase table, methodology and timing data](docs/benchmarks/gemma4-cuda-mtp-ram.md) · [Agent workflow: build, switch and compare CUDA/Vulkan](docs/implementations/engines.md#cuda-and-vulkan)

## REAP, APEX and individual expert placement

On a rented **RTX 4500 Ada 24 GB / Threadripper PRO 5995WX**, we rebuilt Gemma 4 Heretic through **REAP → BF16 GGUF → fresh imatrix → APEX I-Balanced**. Retaining 124 of 128 experts per layer reduced the GGUF from **19.51 to 18.96 GB (−2.81%)**. Top-k stayed at eight; pruning did not produce a measured decode speedup, and the quality-loss target was not established.

A separate experiment kept the same rebuilt weights and cached **475 hot experts** with a **2,200 MiB VRAM budget**. Bypassing that cache during prefill achieved **32.93 tok/s**, **+8.07%** versus whole-block placement in the same fork, with **3.91% lower full-request time** and **2.43 GiB more RSS**. These are server measurements, not desktop performance claims.

![REAP reduced storage; a separate hot-expert placement experiment improved decode and full-request time, with a host-memory tradeoff.](docs/assets/reap.svg)

[Tools, pinned sources, build commands and evaluation limits](docs/implementations/reap.md) · [Numeric data](docs/benchmarks/reap.csv)

## Jev, browser-use and MCP

Keep text generation local and use optional **Jev / TypeSafe API** calls for typed decisions: routing, choosing observed browser actions and checking results. Our integration combines Jev with a local field-text helper and the harness's existing tool loop. Native llama UI MCP can reuse selected Hermes tools and skill text; it does not inherit the complete Hermes harness.

[Jev API example and browser-use architecture](docs/interfaces/jev.md) · [Pinned browser-use and Cua source review](docs/interfaces/jev.md#upstream-implementations-browser-use-and-cua) · [Reuse Hermes tools and skills in llama UI](docs/interfaces/llama-ui.md#reuse-hermes-tools-and-skills)

## Documentation

[Agent skill](SKILL.md) · [Framework manual](docs/README.md#agent-manual) · [English documentation](docs/README.md) · [Launch profiles](docs/README.md#launch-profiles) · [Measurement methodology](docs/README.md#resource-use-and-methodology) · [Comparison details](docs/README.md#comparison-with-colibri-and-freetoken)

All report graphics use the project's monochrome style and English labels. [Artwork sources and regeneration](docs/assets/README.md) keep numbers tied to the benchmark data. Different machines, artifacts and workloads are named explicitly; these reports do not establish a universal speed or quality lead over other frameworks.
