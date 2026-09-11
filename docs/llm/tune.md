# Level 2 — tune a stack and adapt a model

[Documentation](../README.md) · [Validation](../validation.md)

Start from the saved profile and a repeatable workload. State the objective: more context, lower RAM/VRAM, faster prompt processing, faster generation, better tool use or a deliberate model modification. Keep the baseline available and change one consequential variable at a time where practical.

## Settings have different owners

| Change | Owner | Usual application |
|:--|:--|:--|
| Temperature, sampling, output limit | Request/client or server default | Next request; inspect the request actually sent |
| Context, concurrency, device placement, threads, KV precision | Inference runtime | Restart or a documented runtime reconfiguration |
| History, compaction threshold, tool definitions, retry policy | Agent harness | Client/session configuration |
| Experts selected per token or architecture metadata | Model and architecture-specific runtime | Explicit experiment after checking implementation support |
| Tensor precision, expert/layer pruning, merged adapters | Model artifact | New output artifact through [level 3](build.md) |

Changing a server default has no effect if the client overrides it. Changing a client context declaration does not allocate more server memory. Editing an APEX tensor-type recipe does not alter an already-created GGUF.

## Runtime tuning with llama.cpp as an example

Use the selected engine's own parameters. The examples below are grounded in the [server reference](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/server/README.md); check them against the installed binary.

| Knob | Meaning and decision |
|:--|:--|
| `--ctx-size`, `--parallel` | Requested context and concurrent slots; inspect effective per-slot capacity rather than assuming a division rule across releases |
| `--gpu-layers`, `--device` | GPU placement and devices; confirm the loading log and observed memory |
| `--n-cpu-moe N` | Keep MoE weights of the first N layers on CPU; N counts layers, not active experts |
| `--n-cpu-ffn N` | Keep dense FFN weights of the first N layers on CPU; available in the inspected b10883 server; verify tensor matches and allocations |
| `--override-tensor` | Place matching tensors in a supported backend buffer; inspect exact tensor names and precedence before combining overrides |
| `--threads`, `--threads-batch` | CPU work for generation and prompt processing; benchmark, since more threads can increase contention |
| `--batch-size`, `--ubatch-size` | Logical and physical prompt batches; affect scratch memory, prompt speed and multimodal processing |
| `--cache-type-k`, `--cache-type-v` | KV precision; support and quality depend on architecture/backend |
| `--flash-attn` | Attention implementation; check support together with cache types |
| `--load-mode` | Weight loading strategy; file-backed mappings trade memory pressure against page faults and I/O |
| `--cache-ram`, `--ctx-checkpoints` | Reuse/checkpoint storage with additional resource costs |
| `--fit` | Automatic fitting of eligible settings; explicit overrides may constrain what it can adjust |

A useful order is: establish correct output → fit weights with headroom → set the required context and output allowance → tune placement and KV format → tune prompt batches and threads → test real concurrency. If an engine's native auto-tuning already solves the task, keep it and record the effective result.

For a dense model larger than free VRAM, compare whole-layer placement with `--gpu-layers all --n-cpu-ffn N`, choosing N from the tensor budget and confirming the loading log. The latter can retain attention and recurrent tensors on the GPU while selected FFNs execute on CPU. It preserves the model architecture and does not provide MoE's sparse per-token computation. More available RAM makes a placement possible; CPU memory bandwidth, quant kernels and synchronization still determine its speed.

The dense-FFN option was checked against b10883's `--help` and [argument implementation at 91f6a6cf3](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf3/common/arg.cpp). Check the actual executable: `llama-bench` and `llama-server` may expose different options in the same release. Compare placements with the same quant, workload, context, cache types and headroom before changing quantization. Test speculative/MTP decoding separately when the model and backend support it; its extra memory and draft acceptance may improve or reduce throughput.

Use resource limits only with their actual meaning. A systemd `MemoryMax` limit includes cgroup-charged cache and can kill the service; it is not a model compressor, a RAM reservation or a process-RSS measurement. Follow the working [Gemma example](../README.md#gemma) only when its assumptions match.

## Context is a whole-stack setting

Budget system instructions, tool schemas, history, retrieved files, image tokens, reasoning and generated output. Configure the harness for the server's effective context per request and leave room for the response and compaction operation. Keep request timeouts compatible with long prompt processing.

Increasing context can increase KV/state and working-buffer memory, but hybrid/recurrent architectures do not all scale like a conventional full-attention transformer. Inspect the model and the actual allocation, then test near the requested window. Do not multiply our Qwen measurements into a universal estimate.

Compaction summarizes/replaces history; cache reuse avoids recomputing eligible input. They solve different problems. A session can cumulatively process more than 32K tokens while every individual request remains within 32K.

Changing RoPE or context metadata does not establish trained long-context quality. Treat extension beyond documented support as a separate experiment with long-input evaluation.

## Changing the MoE itself

MoE routing chooses a subset of available experts for each token. Moving expert weights to CPU preserves that routing decision. Reducing the selected-expert count may change computation and quality but does not remove stored expert tensors or automatically reduce file size.

For an explicitly requested routing experiment:

1. Inspect the exact GGUF architecture key, expert counts, tensor dimensions and model graph. In llama.cpp, start with `src/llama-model.cpp` and the matching file in `src/models/`.
2. Trace whether the graph reads the override, whether tensor shapes remain valid, and any shared experts or normalization assumptions. A flag accepted by the parser is insufficient.
3. If supported, try a separate launch profile using that architecture's metadata override. The generic form is `--override-kv ARCH.expert_used_count=int:N`; `ARCH` and `N` must come from this inspection, not a copied Qwen example.
4. Compare task quality, routing behavior, speed and memory against the unchanged model. Retain the baseline unless the candidate meets the requested tradeoff.

The inspected llama.cpp quantizer also supports metadata overrides and layer pruning when writing a new artifact. That does not establish support for arbitrary expert deletion. Actual pruning must keep tensor slices, router outputs, indexes, dimensions and metadata consistent; use an existing implementation for that architecture and evaluate it. A learned router cannot be replaced with a generic “pick fewer experts” rule without changing model behavior. See [quantizer source](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/quantize/quantize.cpp) and [model loading](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/src/llama-model.cpp).

For custom precision allocation on this PC, use the [APEX recipe workflow](../implementations/apex.md). For a different method, inspect its own implementation and produce a new artifact through [level 3](build.md).

## Accept or reject the change

Save the before/after settings, workload and [measurements](../validation.md). Reject candidates that fail required tool use, long-input behavior or quality even if decode improves. Stop an unproductive search once the task is met or the documented candidates fail its constraints; explain the concrete limiting resource and next viable option.
