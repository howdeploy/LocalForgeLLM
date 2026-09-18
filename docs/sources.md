# Source map and verification scope

[Documentation](README.md)

The initial implementation review was on **September 10, 2026**, with dated follow-ups below through **September 18**. The pinned snapshots make these guides reviewable; they are not a mandate to downgrade or upgrade a working installation. At execution time, identify the installed release and check changes before using a command or code map.

| Project | Inspected source | Main entry points |
|:--|:--|:--|
| llama.cpp / llama UI | [41fc7584f0c1](https://github.com/ggml-org/llama.cpp/tree/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f) | `docs/build.md`, `tools/server/`, `tools/quantize/`, `tools/imatrix/`, `tools/ui/`, `src/models/` |
| llama.cpp b10883 placement follow-up, September 11, 2026 | [91f6a6cf3](https://github.com/ggml-org/llama.cpp/tree/91f6a6cf3) | Installed server/bench `--help`, `common/arg.cpp`, `common/common.h`, `src/llama-model.cpp`, `src/models/qwen35.cpp`; dense-FFN placement and graph, not a new model throughput result |
| llama.cpp CUDA/Vulkan follow-up, September 11, 2026 | [b10883 build guide](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/docs/build.md), [kernel cgroup v2 memory interface](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files) | Local pinned checkout: `docs/build.md`, `ggml/CMakeLists.txt`, `ggml/src/ggml-cuda/CMakeLists.txt`, `tools/ui/CMakeLists.txt`; successful local CUDA build and device discovery, compile-resource record and [sanitized session timings](benchmarks/gemma4-cuda-mtp-ram.md). Generic build examples are source-checked, not fresh builds performed for this documentation update |
| llama.cpp MTP follow-up, September 11, 2026 | [b10883 / 91f6a6cf36138](https://github.com/ggml-org/llama.cpp/tree/91f6a6cf361385700bbe15981f0f39909df77498) | `common/speculative.cpp`, `common/common.cpp`, `common/arg.cpp`, `common/common.h`, `src/models/qwen35.cpp`, `src/models/delta-net-base.cpp`, `src/llama-sampler.cpp`, server and Vulkan dispatch; [MTP guide](implementations/mtp.md) includes upstream issue/patch status, not a claim of a verified local MTP fix |
| Gemma assistant and artifact follow-up, September 11, 2026 | [b10883 assistant source](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/gemma4-assistant.cpp), [Unsloth head revision](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/tree/c099eb48e663fd284577b04978a94ffccb261841/MTP) | Assistant dimensions, target KV sharing, exact artifact bytes/SHA-256, native enable/disable flags; [download recipe](implementations/mtp.md#download-a-compatible-head) |
| APEX | [636cec7e3f8d](https://github.com/localai-org/apex-quant/tree/636cec7e3f8d308e4162ab2bd5ec4b56807dd806) | `scripts/generate_config.sh`, `scripts/quantize.sh`, sensitivity/allocation scripts |
| Ornith custom Q8 / September 12 | [BF16 GGUF revision 12393612](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B-GGUF/tree/12393612fd4f730ff5aadc23e9b8f9648aa49ceb) | Saved APEX custom recipe, 753 tensor rules, integrity/download verification and local resource report; [Q8 build and failed residency tradeoff](implementations/apex.md#recorded-custom-q8-build-ornith). No REAP, no imatrix, no independently reproduced parent-to-BF16 conversion |
| Cerebras REAP / September 12 experiment | [1970473c51ca](https://github.com/CerebrasResearch/reap/tree/1970473c51ca3caeb98c10392f15b3a08a672974) | `src/reap/pruning_metrics.py`; local Gemma 4 observer/export adapter and self-check; [REAP → APEX build and quality limits](implementations/reap.md) |
| Individual expert cache / September 12 | [adrianhoehne fork, 018789c](https://github.com/adrianhoehne/llama.cpp/tree/018789cb57128ab67bc0bdbda59ae99f4df3f046) | Corrected strided top-k profiling; static hot cache, prefill bypass, 40 measured requests; [sanitized aggregate CSV](benchmarks/reap.csv). Requires the recorded local reader correction for profiling |
| Bonsai 2 / September 18 | [model revision 6ed5e12](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/tree/6ed5e12bf84b7a63069882c91dd9e9218647d17b), [PrismML runtime d8f26eec](https://github.com/PrismML-Eng/llama.cpp/tree/d8f26eec76da6d09bb708bcba51ef64b8cd868a3) | Locally downloaded model card, file manifests, runtime help/logs, native KV mean-centering and saved API checks; [packing and launch recipe](implementations/bonsai.md) |
| Jev / September 18 | [TypeSafe API](https://docs.typesafe.ai/api), [models](https://docs.typesafe.ai/models), [launch article, September 15](https://typesafe.ai/blog/introducing-system-one-models-and-jev) | HTTP schema, `jev-1.13.0` and moving aliases, typed outputs, input limits and vendor pricing/latency; [integration guide](interfaces/jev.md). No new paid call or vendor benchmark rerun |
| Jev browser-use / September 18 | [browser-use/jev-ultrafast, 452c1ad](https://github.com/browser-use/jev-ultrafast/tree/452c1ad2dd628008f1d5608f28158d76e49e6cc0) | Pinned upstream `agent.py`, `browser.py`, `snapshot.js`, `model.py`, `questions.py`, author performance report and local host adapter; [source walkthrough and adaptation boundaries](interfaces/jev.md#upstream-implementations-browser-use-and-cua) |
| Cua / September 18 | [trycua/cua, 05f29785](https://github.com/trycua/cua/tree/05f29785b508a4441ec3aa06c556a8e8b26c1d71) | Driver README, Linux MCP contract, `cua-driver-core/src/browser/tools.rs` and `engine.rs`: exact bindings, current refs and mutation checks; [proposed Jev mapping](interfaces/jev.md#where-cua-fits). Source review only; no Cua installation or browser execution |
| Bonsai llama UI MCP / September 18 | [PrismML server source](https://github.com/PrismML-Eng/llama.cpp/tree/d8f26eec76da6d09bb708bcba51ef64b8cd868a3/tools/server) | Installed help, server MCP schema and text-result handling; recorded 47-tool listing and actual skill lookup/read cycle; [interface boundary](interfaces/llama-ui.md#reuse-hermes-tools-and-skills) |
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

The [Bonsai report](benchmarks/bonsai.md) adds six unique community runs from **ap3x0s** and three selected local timing rows. The subscriber supplied aggregate HTML, not raw logs; the source hash and reported-unit limitations are recorded. RTX 5070 / PQ2_0 results remain separate from RTX 4060 / PTQ1_0. The latter includes a 31,018-token lookup and memory sampling, plus the original reasoning-assertion failure and corrected rerun.

Its separate [interactive-session CSV](benchmarks/bonsai-session.csv) records
nine completed generations and one cancelled stream: 7,355 output tokens and
19.58 tok/s weighted decode. Reasoning-token and tool-call counts from that user
conversation are unavailable. The report separately labels the saved reasoning,
two-call MCP skill loop and local field-text checks; no conversation content is
published. Model shutdown was verified without starting new inference.

The [REAP/APEX record](implementations/reap.md) documents a completed rented-server build, rather than an unrun generic recipe. Its seven aggregate CSV rows separate the 32-request ABBA chat benchmark from 40 expert-cache timing trials. The quality target was not established; the artifact remained experimental. No rented-server speed is relabeled as an RTX 4060 result.

The September 18 graphics refresh recalculates phase means and ratios from the tracked data with [the offline generator/check](../scripts/render_benchmarks.py). Existing assets retain English labels and the project's monochrome design. Local documentation links, embedded command syntax and SVG structure can be checked without running inference. PNG export is artifact generation; no visual/UI review or live Jev browser trial is claimed for this documentation task.

The framework documents three kinds of evidence:

- **Measured:** the named existing deployment runs and their stated workloads/resource definitions.
- **Source-checked:** configuration fields, command forms, architecture maps and implementation-specific behavior at the linked revision.
- **To validate on the target:** performance, quality, backend compatibility, a complete new installation, a custom weight build or an interface extension.

Writing these guides does not establish that every documented engine/interface combination was installed and run. For a real stack task, use the [validation procedure](validation.md) and replace estimates with measurements in its local record.

Documentation checks covered local links/anchors, shell syntax, JSON/YAML examples and paths in the pinned source trees. The documented custom APEX generator command was also executed without model weights: it emitted 680 tensor rules, with the requested expert precision verified across all 40 example layers. This checks recipe generation, not quantization quality or model performance.

## Refresh the knowledge

When a relevant component changes, inspect its release/configuration diff and the code paths linked by its guide. Update the command, code map and source revision together, then verify the affected task. Keep migration notes where users may have the older working setup, especially OpenShell's managed-route versus native-provider distinction. Do not update only a version label while retaining obsolete behavior.
