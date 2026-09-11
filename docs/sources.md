# Source map and verification scope

[Documentation](README.md)

Implementation documentation and relevant source paths were inspected on **September 10, 2026**. The pinned snapshots make these guides reviewable; they are not a mandate to downgrade or upgrade a working installation. At execution time, identify the installed release and check changes before using a command or code map.

| Project | Inspected source | Main entry points |
|:--|:--|:--|
| llama.cpp / llama UI | [41fc7584f0c1](https://github.com/ggml-org/llama.cpp/tree/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f) | `docs/build.md`, `tools/server/`, `tools/quantize/`, `tools/imatrix/`, `tools/ui/`, `src/models/` |
| llama.cpp b10883 placement follow-up, September 11, 2026 | [91f6a6cf3](https://github.com/ggml-org/llama.cpp/tree/91f6a6cf3) | Installed server/bench `--help`, `common/arg.cpp`, `common/common.h`, `src/llama-model.cpp`, `src/models/qwen35.cpp`; dense-FFN placement and graph, not a new model throughput result |
| llama.cpp CUDA/Vulkan follow-up, September 11, 2026 | [b10883 build guide](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/docs/build.md), [kernel cgroup v2 memory interface](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files) | Local pinned checkout: `docs/build.md`, `ggml/CMakeLists.txt`, `ggml/src/ggml-cuda/CMakeLists.txt`, `tools/ui/CMakeLists.txt`; successful local CUDA build and device discovery, compile-resource record and [sanitized session timings](benchmarks/gemma4-cuda-mtp-ram.md). Generic build examples are source-checked, not fresh builds performed for this documentation update |
| llama.cpp MTP follow-up, September 11, 2026 | [b10883 / 91f6a6cf36138](https://github.com/ggml-org/llama.cpp/tree/91f6a6cf361385700bbe15981f0f39909df77498) | `common/speculative.cpp`, `common/common.cpp`, `common/arg.cpp`, `common/common.h`, `src/models/qwen35.cpp`, `src/models/delta-net-base.cpp`, `src/llama-sampler.cpp`, server and Vulkan dispatch; [MTP guide](implementations/mtp.md) includes upstream issue/patch status, not a claim of a verified local MTP fix |
| Gemma assistant and artifact follow-up, September 11, 2026 | [b10883 assistant source](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/gemma4-assistant.cpp), [Unsloth head revision](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/tree/c099eb48e663fd284577b04978a94ffccb261841/MTP) | Assistant dimensions, target KV sharing, exact artifact bytes/SHA-256, native enable/disable flags; [download recipe](implementations/mtp.md#download-a-compatible-head) |
| APEX | [636cec7e3f8d](https://github.com/localai-org/apex-quant/tree/636cec7e3f8d308e4162ab2bd5ec4b56807dd806) | `scripts/generate_config.sh`, `scripts/quantize.sh`, sensitivity/allocation scripts |
| FreeToken | [fb7f732de08a](https://github.com/FlashML-org/FreeToken/tree/fb7f732de08a3247c397f90d932f7e69b9f63600) | `docs/install.md`, `docs/cli.md`, `docs/models.md`, `python/freetoken/` |
| FreeToken Gemma comparison follow-up, September 11, 2026 | [0ffd5c8b2941 model guide](https://github.com/FlashML-org/FreeToken/blob/0ffd5c8b2941974ed64dec09170b19259e2ba5aa/docs/models.md), [issue #188](https://github.com/FlashML-org/FreeToken/issues/188) | Text-only serving of multimodal checkpoints; separate author-reported patched 16 GB GPU result, not a local or official 8 GB benchmark |
| Colibri | [fd93c41aa6ae](https://github.com/JustVugg/colibri/tree/fd93c41aa6ae2c7d1cc1a1e2d6b79dbe6d341708) | Family guides, `c/coli`, family engine/converter |
| Pi | [4bd3f48df0b1](https://github.com/earendil-works/pi/tree/4bd3f48df0b14c82e8df2640645e94f82f125f44) | `packages/coding-agent/`, `packages/agent/`, `packages/ai/`, `packages/tui/` |
| OpenShell | [a0814443f19c](https://github.com/NVIDIA/OpenShell/tree/a0814443f19c07102b19ff09d6ead3d3ba59f9c5) | `docs/sandboxes/`, `docs/providers/`, `architecture/`, gateway/supervisor crates |
| Hermes | [67764dc08633](https://github.com/NousResearch/hermes-agent/tree/67764dc0863349a384c16425e73ee8571f3a94b7) | `website/docs/`, `agent/`, `hermes_cli/`, `tools/`, `web/`, `apps/desktop/` |

The [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli) and [MLX-LM](https://github.com/ml-explore/mlx-lm) are additional discovery references. Inspect their selected versions before installing or integrating them.

## Existing measured stack

The [Qwen/Gemma examples](README.md#launch-profiles) preserve the working llama.cpp **b10883** configurations and their measurements. The legacy OpenShell/Pi connection uses **OpenShell 0.0.110** and **Pi 0.84.2**. Current source maps are separate from those previously measured versions.

The September 11 [Gemma MTP case study](benchmarks/gemma4-mtp.md) adds three sanitized timing rows: one no-MTP request and two MTP requests. It verifies 14.83 tok/s weighted MTP decode and 15.03 tok/s over a 102.05-second decode interval. It does not establish a causal +51.1% MTP gain, quality parity, MTP vision/tool support or performance on a filled 32K context. The comparison links primary benchmark reports and explicitly separates their hardware, quantization and methodology. Raw sessions and machine paths remain local.

The later [CUDA/MTP/RAM report](benchmarks/gemma4-cuda-mtp-ram.md) covers 19 completed responses across eight phases; its first three timing rows overlap that MTP case study. It records the backend transition, RAM-cap and MTP changes, 18.80 tok/s weighted decode in the four-response CUDA/MTP/20-GiB phase and 10 min 30.161 s for the initial CUDA compilation. Workload/cache differences prevent isolating a CUDA-only gain; compilation excludes other setup work. The [reusable backend workflow](implementations/engines.md#cuda-and-vulkan) keeps those distinctions explicit.

The framework documents three kinds of evidence:

- **Measured:** the named existing deployment runs and their stated workloads/resource definitions.
- **Source-checked:** configuration fields, command forms, architecture maps and implementation-specific behavior at the linked revision.
- **To validate on the target:** performance, quality, backend compatibility, a complete new installation, a custom weight build or an interface extension.

Writing these guides does not establish that every documented engine/interface combination was installed and run. For a real stack task, use the [validation procedure](validation.md) and replace estimates with measurements in its local record.

Documentation checks covered local links/anchors, shell syntax, JSON/YAML examples and paths in the pinned source trees. The documented custom APEX generator command was also executed without model weights: it emitted 680 tensor rules, with the requested expert precision verified across all 40 example layers. This checks recipe generation, not quantization quality or model performance.

## Refresh the knowledge

When a relevant component changes, inspect its release/configuration diff and the code paths linked by its guide. Update the command, code map and source revision together, then verify the affected task. Keep migration notes where users may have the older working setup, especially OpenShell's managed-route versus native-provider distinction. Do not update only a version label while retaining obsolete behavior.
