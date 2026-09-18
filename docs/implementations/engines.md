# Choose an inference implementation

[Documentation](../README.md) · [Discovery procedure](../agent-workflow.md#learn-an-implementation) · [Source revisions](../sources.md)

Choose the engine and checkpoint together. This catalog gives concrete starting points; it does not restrict the framework to these projects or establish support for every model they resemble.

| Implementation | Candidate use | Verify before selecting |
|:--|:--|:--|
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | GGUF on CPU/GPU backends, explicit placement, local API and bundled chat UI | Architecture, quantization/backend kernels, template and modality support in the exact build |
| [PrismML llama.cpp](https://github.com/PrismML-Eng/llama.cpp) | Ternary Bonsai GGUF with native packed kernels and matching activation transforms | [PTQ1_0 vs PQ2_0, cache calibration and actual memory fit](bonsai.md); stock format support must not be assumed |
| [Static expert-cache fork](https://github.com/adrianhoehne/llama.cpp/tree/018789cb57128ab67bc0bdbda59ae99f4df3f046) | Experimental per-expert GPU residency over CPU-backed MoE weights | [Corrected profiling, prefill bypass, runtime fallback and extra RAM cost](reap.md#separate-experiment-hot-experts-on-gpu-cold-experts-in-ram) |
| [FreeToken](https://github.com/FlashML-org/FreeToken) | Supported MoE checkpoints with expert offload/cache and CPU/GPU execution strategies | Model/quantization matrix, CUDA/driver requirements, host RAM and the supported checkpoint conversion path |
| [Colibri](https://github.com/JustVugg/colibri) | Its supported model families and converted containers, with family-specific CPU/GPU/storage behavior | Exact family engine, converter, memory semantics and server/tool support |
| [MLX-LM](https://github.com/ml-explore/mlx-lm) | An alternative to investigate for supported models on Apple Silicon | Architecture, MLX checkpoint/quantization, unified memory and required serving features |

Other engines can be chosen through the same discovery procedure. Read their original documentation, retain the relevant configuration/code map in the stack record and run the workload. A published speed advantage is a reason to test a candidate, not a reason to silently replace a working stack.

## llama.cpp

Use [installation](../llm/install.md), [tuning](../llm/tune.md) and [building](../llm/build.md). The native tools cover serving, conversion, quantization, calibration and measurement without a LocalForgeLLM-specific inference wrapper.

Read the following paths at the selected revision:

| Path | Reason to inspect |
|:--|:--|
| `docs/build.md`, `common/arg.cpp` | Backend build requirements and real CLI flags/defaults |
| `src/llama-model.cpp`, `src/models/` | Architecture metadata, tensors and computation graph |
| `tools/server/server-context.cpp` | Slots, request scheduling and inference state |
| `common/speculative.cpp`, `common/common.h`, `src/models/delta-net-base.cpp` | [MTP](mtp.md): head/context initialization, draft sampling and recurrent rollback state |
| `src/models/gemma4-assistant.cpp`, `src/models/gemma4.cpp` | Separate Gemma MTP assistant, target dimensions and shared KV; [agent operations](mtp.md#operate-an-existing-stack) and [measured case](../benchmarks/gemma4-mtp.md) |
| `tools/server/server-chat.cpp` | Chat request/template and response handling |
| `tools/quantize/quantize.cpp`, `src/llama-quant.cpp` | Weight transformation flags and actual buffer/tensor processing |
| `tools/ui/` | [Bundled UI and its agent/tool integration](../interfaces/llama-ui.md) |

APEX is an optional way to generate tensor-precision recipes for this toolchain. Published APEX weights do not require the APEX scripts at inference time.

### CUDA and Vulkan

These are llama.cpp execution backends. When both implement the selected architecture and tensor types, the same GGUF can run through either backend. Switching the runtime/device is a level-2 operation; it does not require training, conversion or requantization. Verify projector and MTP support separately. Another engine or checkpoint format may have a different contract.

On NVIDIA hardware, consider CUDA and Vulkan when supported instead of assuming either is always faster. Inspect the actual GPU, free VRAM, CPU/RAM budget, driver and existing builds. For a CUDA source build, verify the toolkit, `nvcc`, supported host compiler and GPU compute capability; the driver's advertised CUDA version alone does not establish that the toolkit is installed. Vulkan needs the matching driver and build dependencies. Use the [pinned b10883 build guide](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/docs/build.md) and the selected revision's CMake/source, not package names copied from another OS.

Prefer a compatible official binary. If a source build is needed, retain the working runtime and use a separate build directory. These Linux examples run from a verified llama.cpp source checkout after installing the selected backend's dependencies. Build only the candidate required by the task:

```bash
cmake -S . -B build-cuda -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON -DGGML_VULKAN=OFF -DCMAKE_CUDA_ARCHITECTURES=89
cmake --build build-cuda --config Release --target llama-server --parallel 4
```

```bash
cmake -S . -B build-vulkan -DCMAKE_BUILD_TYPE=Release \
  -DGGML_VULKAN=ON -DGGML_CUDA=OFF
cmake --build build-vulkan --config Release --target llama-server --parallel 4
```

Architecture `89` is the RTX 4060 example; select the actual GPU's supported value before reusing it. Four workers are a build budget, not an inference setting. For a backend comparison, use the same source revision and equivalent CPU optimization settings, and record compiler, build flags and dependency versions. A prebuilt-versus-native comparison can also include compiler/CPU-kernel differences. Start with upstream kernel defaults before forcing MMQ or cuBLAS. If the existing binary already contains both backends, device selection may be sufficient; rebuilding is not mandatory.

Preserve the compatible llama UI assets when rebuilding a UI stack; inspect `tools/ui/CMakeLists.txt` and the asset version/checksum. Keep a user-local toolkit's shared libraries available to the runtime. On Linux, check both the executable and dynamically loaded GPU backend libraries with `ldd`; use the build's runtime search path, such as `CMAKE_BUILD_RPATH`, when required. A successful link does not prove GPU discovery.

Select the candidate executable and perform non-inference checks:

```bash
candidate_server=./build-cuda/bin/llama-server
"$candidate_server" --version
"$candidate_server" --list-devices
```

Read its `--help` and use the returned device ID. `CUDA0` and `Vulkan0` are examples, not universal device names. These checks do not load the model or establish serving speed.

For an authorized switch, copy the effective launch configuration, change the executable/device and preserve the model, template, projector, alias, endpoint, context, CPU expert/FFN placement, threads, batches, KV precision, load mode, RAM cap and MTP settings. Translate backend-specific tensor-buffer names only after checking their equivalent placement. Confirm an idle slot, stop/start through the existing process manager and verify startup allocations, health and effective settings. A restart clears the server's in-memory cache, so history reprocessing must not be counted as a steady-state backend regression. Keep the original runtime/profile as the rollback target.

Compare one factor at a time with the same representative workload:

| Question | Change | Hold fixed |
|:--|:--|:--|
| CUDA or Vulkan? | Runtime backend/device | Model, CPU/GPU placement, RAM cap, MTP, context, cache policy, sampler and workload |
| Does more RAM help? | Service memory ceiling | Backend, placement, load mode, MTP and workload |
| Does MTP help? | Speculation mode and its required head/settings | Backend, main placement, RAM cap and workload |
| Can rebalancing improve the stack? | One placement/thread/batch setting per trial | Selected backend and the other settings; report a tuned-stack result |

Repeat/interleave only enough runs to resolve the decision, with matched warm-up and actual context fill. Record prompt processing, decode, total latency, output quality, RAM/VRAM and paging; different chat requests provide descriptive session data, not an isolated causal gain. If the user runs inference tests themselves, prepare the comparison and read completed timings without sending generation requests. Follow [validation](../validation.md).

For a model larger than VRAM, budget CPU weights and file cache as well as GPU tensors, KV and scratch buffers. Under Linux cgroup v2, inspect changes in `memory.events`, `memory.stat` (including `pgmajfault` and `workingset_refault_file`) and system available RAM. Raising a restrictive cap can reduce reclaim/refaults when physical memory is available; it does not make CPU-resident weights GPU-resident. Record the cap separately from measured usage, and retain headroom for other applications. See the [kernel memory-controller definitions](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory-interface-files).

The [Gemma CUDA/MTP/RAM case study](../benchmarks/gemma4-cuda-mtp-ram.md) records 19 completed responses, an initial Vulkan-to-CUDA change from 14.83 to 14.01 tok/s, and later CUDA + MTP sessions at 18.80 tok/s with a 20 GiB cap. It does not establish a CUDA-only speedup. Initial compilation took 10 min 30.161 s with four workers and 2.1 GiB peak build memory; downloads, configuration and validation were additional, unmeasured setup time. For a new build, record those phases separately and report compilation as runtime work, not model conversion.

## FreeToken

The inspected [installation guide](https://github.com/FlashML-org/FreeToken/blob/fb7f732de08a3247c397f90d932f7e69b9f63600/docs/install.md) specifies Linux x86_64, NVIDIA driver r580+/CUDA 13 and Python 3.10+. JIT kernel compilation requires the matching toolkit/`nvcc`. These are requirements of that source snapshot, not requirements of LocalForgeLLM. Inspect the current platform guide before selecting Windows/WSL or another release.

Inside a dedicated environment, install the selected package version with the acceleration extra, or use an exact source checkout and its dependencies. Pin matching runtime/kernel-cache wheel identities if using nightlies; the rolling tag alone is not reproducible.

For a supported local checkpoint directory:

```bash
ft --version
ft serve --model "$MODEL_DIR" --served-model-name localforge-model \
  --host 127.0.0.1 --port 1919 --max-running-requests 1
```

Discover the model at `http://127.0.0.1:1919/v1/models`. Then connect the chosen client with that base URL and ID. See [quick start](https://github.com/FlashML-org/FreeToken/blob/fb7f732de08a3247c397f90d932f7e69b9f63600/docs/quickstart.md).

Key native controls in the inspected [CLI reference](https://github.com/FlashML-org/FreeToken/blob/fb7f732de08a3247c397f90d932f7e69b9f63600/docs/cli.md): context via `--max-seq-len-override`; VRAM via `--memory-ratio`; expert execution via `--moe-strategy`; expert cache via `--moe-cache-size`/`--moe-cache-rate`/automatic sizing; KV headroom via `--kv-reserve-tokens`; CPU work via `--moe-cpu-threads`; request parsers via `--tool-call-parser` and `--reasoning-parser`. Mutually exclusive overrides must not be combined. Use `ft bench bw` when a hardware bandwidth profile is needed for its hybrid strategy, and `ft ctl stats`/`ft ctl cache` for its native measurements.

Read `docs/models.md` and the corresponding architecture/backend under `python/freetoken/` before changing execution or formats. `ft checkpoint` builds FTW artifacts from its supported HF checkpoint path. This does not mean an arbitrary APEX GGUF is accepted or that FTW is a llama.cpp format.

`ft launch` can configure/install supported agent CLIs and mutate their provider files. Preview with its `--dry-run` and preserve existing client settings. Pi can instead be connected through its ordinary [custom-provider configuration](../interfaces/pi.md); it does not need a FreeToken-specific launcher entry.

## Colibri

The launcher chooses a family-specific engine using the model configuration. Read that family's guide before applying generic flags. A concrete example is [Qwen3.6](https://github.com/JustVugg/colibri/blob/fd93c41aa6ae2c7d1cc1a1e2d6b79dbe6d341708/docs/qwen36.md), which uses Colibri's converted int4 container, not a GGUF file.

After downloading a compatible pinned container, the documented CPU build and terminal connection are:

```bash
make -C c qwen36
COLI_MODEL="$MODEL_DIR" ./c/coli chat
```

`./c/coli serve` selects the corresponding API path; inspect its help for bind/port and discover the model ID before configuring a client. The optional CUDA tier uses the family's documented build and memory controls. Read [the CUDA-tier guide](https://github.com/JustVugg/colibri/blob/fd93c41aa6ae2c7d1cc1a1e2d6b79dbe6d341708/docs/qwen36-cuda-tier.md) for that path.

A consequential current exception: the Qwen3.6 guide states that `coli --ram` is not honored by this engine; its expert set requires full RAM residency for the CUDA-tier path. Do not promise disk-streaming RAM limits based on another Colibri family's behavior.

For modifications, begin with `c/coli`, `c/qwen36.c`, `c/tools/convert_qwen36.py` and the family guide. Trace the relevant setting into the selected engine. Validate output and tool compatibility, then compare against the same task on other engines.
