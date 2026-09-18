# Bonsai 2 — ternary weights and GPU cache placement

[Documentation](../README.md) · [Measured results](../benchmarks/bonsai.md) · [Engine selection](engines.md)

This is the **dense, hybrid-attention Ternary Bonsai 2 27B** derived from Qwen3.8-27B. MoE expert-offload flags from Gemma are not its tuning mechanism. Use a runtime implementing both its packing and Hadamard activation transform. Our stock b10883 could not load the selected artifact; the verified runtime is the [PrismML fork at d8f26eec](https://github.com/PrismML-Eng/llama.cpp/tree/d8f26eec76da6d09bb708bcba51ef64b8cd868a3), reporting b10683, built for CUDA 13.3.

## Select the actual packing

| Component | Local artifact | Bytes |
|:--|:--|--:|
| Language model | `Ternary-Bonsai-2-27B-PTQ1_0.gguf` | 5,946,648,928 |
| Optional vision | `Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf` | 629,246,976 |
| Local K-cache calibration | `Ternary-Bonsai-2-27B-PTQ1_0-kv-bias.gguf` | 66,400 |

Model plus projector is **6.58 GB / 6.12 GiB on disk**, before runtime, download cache and working space. The community RTX 5070 run instead uses **PQ2_0, 7.21 reported GB**. Do not replace one filename with the other while keeping a memory estimate. The [model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/6ed5e12bf84b7a63069882c91dd9e9218647d17b/README.md) explains dense-trit versus two-bit-slot packing; speed depends on the GPU and kernels.

Download only the selected files, preserving the pinned revision:

```bash
hf download prism-ml/Ternary-Bonsai-2-27B-gguf \
  Ternary-Bonsai-2-27B-PTQ1_0.gguf \
  Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf \
  --revision 6ed5e12bf84b7a63069882c91dd9e9218647d17b \
  --local-dir "$MODEL_DIR"
```

Recorded SHA-256 values:

```text
53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3  Ternary-Bonsai-2-27B-PTQ1_0.gguf
6807ede61d570bb86ba34b756a0fa109edc33668604de867c6ea6d8f1d631903  Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf
2a74291486bac8e3fff95e3380a2e21808631d1ddc8cd1c6d0bf8e8038f7f66a  Ternary-Bonsai-2-27B-PTQ1_0-kv-bias.gguf
```

The last hash identifies our calibration output, not a file to download or the expected hash of a new calibration corpus.

## Calibrate Q4 KV with the matching native tool

The fork supplies `llama-kv-mean-center`. Our 512-token, one-chunk calibration covered the 16 full-attention layers. It is a small compatibility pilot, not proof that Q4 equals Q8/F16 in general. Set `PRISM_BIN`, `MODEL_DIR`, `CALIBRATION_TEXT` and a new `KV_BIAS` output path:

```bash
"$PRISM_BIN/llama-kv-mean-center" \
  -m "$MODEL_DIR/Ternary-Bonsai-2-27B-PTQ1_0.gguf" \
  -f "$CALIBRATION_TEXT" -o "$KV_BIAS" \
  -ngl all --fit off -ctk q4_0 -ctv q4_0 -fa on \
  -c 512 -b 512 -ub 64 -t 6 -tb 6 --chunks 1
```

Provide enough tokenized text for a complete chunk. Our 498-token attempt failed. More importantly, calibration must match the runtime's cache/attention basis: an initially generated bias for a different basis was rejected at load. Recalibration with Q4 K/V and Flash Attention produced the accepted file. Preserve corpus identity, command, model hash and bias hash together.

## Measured 32K profile on RTX 4060 8 GB

This is a portable form of the measured command. Use the matching CUDA libraries for the selected binary. The original service additionally used `MemoryMax=20G`, `MemorySwapMax=0`, `CPUQuota=600%`, `Nice=5` and mmap; the RAM limit is a cap, not a reservation or measured consumption.

```bash
GGML_CUDA_DISABLE_GRAPHS=1 "$PRISM_BIN/llama-server" \
  --model "$MODEL_DIR/Ternary-Bonsai-2-27B-PTQ1_0.gguf" \
  --mmproj "$MODEL_DIR/Ternary-Bonsai-2-27B-mmproj-Q8_0.gguf" \
  --no-mmproj-offload --image-min-tokens 1024 --image-max-tokens 1024 \
  --alias bonsai-local --host 127.0.0.1 --port 8081 --cors-origins localhost \
  --device CUDA0 --gpu-layers all --fit off --load-mode mmap \
  --threads 6 --threads-batch 6 \
  --ctx-size 32768 --parallel 1 --batch-size 512 --ubatch-size 32 \
  --kv-offload --flash-attn on --cache-type-k q4_0 --cache-type-v q4_0 \
  --kv-mean-center "$KV_BIAS" --cache-ram 0 --ctx-checkpoints 1 \
  --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0 \
  --jinja --reasoning on --reasoning-format deepseek --reasoning-effort medium \
  --spec-type none --log-colors off --log-timestamps
```

Open llama UI at `http://localhost:8081`; agent clients use `http://127.0.0.1:8081/v1` and `bonsai-local`. The short benchmark overrides sampling to temperature 0 and `chat_template_kwargs: {"enable_thinking": false}`. Interactive thinking latency therefore need not match that check. Upstream supports `medium` and `xhigh`; `low` is not a supported shorter-thinking setting in this model card.

### Why these settings

- **PTQ1_0** reduces weight residency enough for this 8 GB configuration.
- **GPU Q4 KV and recurrent state** avoid the host placement used by our slow baseline. Flash Attention and the matching bias make this low-memory path usable in the inspected fork.
- **Microbatch 32, one slot, CPU projector and disabled CUDA graphs** constrain working allocations. They are measured profile choices, not individually proven speed improvements. Do not copy Gemma's 1152 microbatch blindly.
- **No MTP:** our Bonsai profile does not load a speculative head. The subscriber's attempted native `draft-mtp` run failed. Gemma's successful MTP head is not compatible merely because both models have “27B-class” names.

The final process snapshot was **6,386 MiB VRAM**; whole-card free memory fell to **98 MiB** during the recorded checks. Recheck available VRAM before launch. If it does not fit, preserve this candidate and restore the saved CPU-cache profile (`--no-kv-offload`, microbatch 64), or test a smaller context under the user's requirements. Do not close unrelated applications automatically.

## The subscriber's 12 GB approach

The supplied report uses PrismML b10685, **PQ2_0 + GPU Q8 KV + Flash Attention**, 32K, one slot, eight threads and continuous batching. Its best run reports 9.74 GB VRAM and 59.65 tok/s over 10K output tokens. F16 KV reports 10.59 GB and 54.69 tok/s. This supports testing a cache-precision tradeoff on that machine; it does not predict a 4060's rate. The 5070 and 4060 profiles differ in packing, kernel revision, cache precision, hardware and workload.

Keep target context, input/output lengths, thinking mode and timing definitions with each result. Use [validation](../validation.md) for text, tools, required vision and long inputs. A 32K profile cannot satisfy a harness that insists on at least 64K; maintain a separate measured profile instead of misreporting the model's advertised context. For optional tools in llama UI, follow [MCP and skills](../interfaces/llama-ui.md#reuse-hermes-tools-and-skills) and [Jev](../interfaces/jev.md).
