# Choose an inference implementation

[Documentation](../README.md) · [Discovery procedure](../agent-workflow.md#learn-an-implementation) · [Source revisions](../sources.md)

Choose the engine and checkpoint together. This catalog gives concrete starting points; it does not restrict the framework to these projects or establish support for every model they resemble.

| Implementation | Candidate use | Verify before selecting |
|:--|:--|:--|
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | GGUF on CPU/GPU backends, explicit placement, local API and bundled chat UI | Architecture, quantization/backend kernels, template and modality support in the exact build |
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
