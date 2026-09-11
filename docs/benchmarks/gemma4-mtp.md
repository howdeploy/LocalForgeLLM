# Gemma 4: deployment comparison and MTP observations

[Project](../../README.md) · [Launch profile](../README.md#gemma) · [MTP operations](../implementations/mtp.md) · [Timing data](gemma4-mtp.csv)

**Evidence reviewed September 11, 2026.** Our Gemma 4 26B-A4B Heretic APEX
I-Balanced deployment measured **14.83 tok/s weighted decode across two MTP
requests**. The longer response sustained **15.03 tok/s over 102.05 seconds of
decode**, with 1535 logged output tokens. The preceding no-MTP request measured
9.81 tok/s. Their **+51.1% observed difference is not a controlled MTP gain**:
the user requests differed. This is a small deployment observation, with formal
quality evaluation pending.

The target is **APEX I-Balanced**, with a **separate Q8_0 MTP assistant**.
It is not a full-Q8 target. APEX controls weight precision; MTP changes the decode
procedure; llama.cpp executes both. LocalForgeLLM's agent selects and configures
these components.

## Comparison scope

![Gemma 4 deployment results, with quantization, hardware and evidence scope shown for each row.](../assets/gemma4-comparison.svg)

These are same-family deployment references, not a ranking on identical hardware.
No external measurement of our exact Heretic APEX artifact on this exact PC was
found in the reviewed sources. Disk sizes below are decimal GB, not live RAM or
VRAM consumption.

| Deployment | Target and additional weights | Hardware / runtime | Decode | Evidence and limits |
|:--|:--|:--|--:|:--|
| **LocalForgeLLM** | Heretic APEX I-Balanced **19.51 GB**, MTP Q8 head **0.46 GB**, CPU vision projector **1.19 GB** | RTX 4060 **8 GB**, Ryzen 5 5600, 32 GB RAM; llama.cpp **b10883 / Vulkan** | **14.83 tok/s** | Two user requests; weighted by decode duration; 32K configured, at most 2265 live context tokens |
| llama.cpp, community CUDA profile | Gemma 4 QAT UD-Q4_K_XL, about **14 GB**, QAT MTP head about **0.25 GB** | RTX 2070 Max-Q **8 GB**, i7-8750H, 31 GB RAM; CUDA, commit `04eb4c4` | **24.0 tok/s** | 32K, temperature 1, draft depth 2; repeated coding test, trimmed mean. [Benchmark](https://github.com/ricardodeazambuja/gemma4-26B-only-8B-VRAM/blob/100afff4859b7bccb7adadfc7c5638136ee9f3dc/docs/mtp-benchmark.md) |
| llama.cpp, community Vulkan profile | Gemma 4 QAT UD-Q4_K_XL, about **14 GB** | Same RTX 2070 Max-Q / i7-8750H rig, Vulkan | **~4.9 tok/s** | Earlier backend comparison; not the CUDA MTP experiment's paired baseline. [Author's setup](https://github.com/ricardodeazambuja/gemma4-26B-only-8B-VRAM/blob/100afff4859b7bccb7adadfc7c5638136ee9f3dc/README.md) |
| Ollama, full-Q8 reference | Gemma 4 26B-A4B **Q8_0**, about **28 GB** as reported | NVIDIA **GB10, 128 GB unified memory**; Ollama **0.20.3**, Docker | **45.2 tok/s** | Author's average across seven informal workloads; no repeated trials. The 1K-output test reports 44.1 tok/s. [Subterra benchmark](https://www.subterratechnologies.com/blog/gemma-4-on-nvidia-gb10-quantization-benchmarks-for-local-inference) |
| FreeToken, larger-GPU reference | Gemma 4 QAT UD-Q4_K_XL; actual tensor types mostly Q4_0 | RTX 4080 SUPER **16 GB**; FreeToken **0.1.2**, CUDA | **179 tok/s reported** | One issue author's report after a local loader patch, described as “at 1200 tokens”; prompt/output split, repetitions and CPU are unspecified. [Issue #188](https://github.com/FlashML-org/FreeToken/issues/188) |

Colibri's [inspected model roster](https://github.com/JustVugg/colibri/blob/fd93c41aa6ae2c7d1cc1a1e2d6b79dbe6d341708/README.md)
does not list Gemma 4. Its nearest reference here is a **different family**:
Qwen3.6 35B-A3B int4, **9.9 tok/s warm**, Threadripper 3945WX + RTX 3070 8 GB,
40 GB peak RSS, 200-token decode. This is not a Gemma result or a zero-speed
result. [Colibri measurement](https://github.com/JustVugg/colibri/blob/fd93c41aa6ae2c7d1cc1a1e2d6b79dbe6d341708/docs/qwen36-cuda-tier.md)

The matched-capacity CUDA result exceeds our observed rate despite an older GPU.
Different target weights, backend, memory policy and workload prevent attributing
that gap to one component. It is a reason to consider a future local CUDA trial
under the same workload; it is not evidence that changing a flag will reproduce
24 tok/s here. None of the external stacks was installed for this comparison.

## Weight size and functionality

| Variant | What it preserves or changes | What has been established |
|:--|:--|:--|
| Our Heretic APEX target + Q8 assistant | Refusal-modified target, mixed tensor precision, text and the configured vision projector | This exact pairing loaded; text decode timings are below. Earlier no-MTP vision use worked; vision with MTP has not been validated |
| Full Gemma 4 26B-A4B Q8_0 | Same base model family, different quantization and behavior from the Heretic target | Unsloth's pinned main file is **26,859,861,728 bytes (26.86 GB)**, before projector/head/runtime allocations. No local full-Q8 speed test |
| QAT Gemma 4 26B-A4B | Quantization-aware target with its matching assistant; distinct from our non-QAT Heretic artifact | Published same-family speed evidence; no local quality parity test |
| FreeToken's Gemma serving path | A different engine and supported tensor format | Its current documentation serves multimodal checkpoints **as text only**; our configured vision path is therefore not functionally interchangeable |

Full-Q8 file size comes from the [pinned Unsloth artifact](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/blob/c099eb48e663fd284577b04978a94ffccb261841/gemma-4-26B-A4B-it-Q8_0.gguf).
FreeToken's modality limitation is documented in its [model guide at `0ffd5c8`](https://github.com/FlashML-org/FreeToken/blob/0ffd5c8b2941974ed64dec09170b19259e2ba5aa/docs/models.md).
Parameter count and bit width alone do not establish equivalent reasoning,
coding, tool use or refusal behavior. This report has no common quality evaluation
across the variants, so it makes no quality ranking.

## Local MTP timings

![Our Gemma MTP session timings and observed difference, alongside published controlled comparisons on a different 8 GB rig.](../assets/gemma4-mtp.svg)

| Mode / request | Newly processed prompt tokens | Logged output tokens | Prompt time | Decode time | Total time | Decode rate |
|:--|--:|--:|--:|--:|--:|--:|
| No MTP / B1 | 100 | 171 | 14.31689 s | 17.32417 s | 31.64106 s | **9.81 tok/s** |
| MTP / M1 | 103 | 300 | 10.88741 s | 21.57908 s | 32.46649 s | **13.86 tok/s** |
| MTP / M2 | 632 | 1535 | 47.28903 s | 102.04708 s | 149.33612 s | **15.03 tok/s** |
| **MTP aggregate** | **735** | **1835** | **58.17644 s** | **123.62616 s** | **181.80261 s** | **14.83 tok/s** |

The runtime excludes the first output token from each request's timed decode
rate: `(1835 - 2) / 123.62616 = 14.82695895`. These are model output tokens,
including any reasoning tokens counted by the runtime, not a count of visible
answer text alone. Newly processed prompt tokens exclude cached history. The
largest reported live context was **2265**, with no truncation reported.
**32K is the configured capacity**, not the input length exercised here.

The two requests accepted **174/250** and **801/1468** drafted tokens:
**975/1718 = 56.75% aggregate acceptance**. Draft attempts are not additional
delivered tokens. The 15.03 rate excludes **47.29 seconds of prompt processing**;
that request took **149.34 seconds total**. Decode speed alone does not describe
time to first token or complete task latency.

### MTP change: observed versus controlled

| Evidence | Without MTP | With MTP | Difference | Interpretation |
|:--|--:|--:|--:|:--|
| Our user session, fixed main placement | 9.81 | 14.83 | **+51.1%** | Different requests; observed gap, not causal gain |
| Published QAT / CUDA, 32K, temperature 1 | 23.1 | 24.0 | **+3.9%** | Within the author's reported noise |
| Published QAT / CUDA, 32K, greedy | 22.9 | 27.1 | **+18.3%** | Repeated paired baseline/candidate test; different hardware and weights |

The external rows use depth 2 and cutoff 0, one coding prompt, seed 42, 256 output
tokens and trimmed means of 5–6 repetitions. The author estimates a ±13% noise
threshold. Percentages here are recomputed from the displayed rates; the source
rounds them to +4% and +19%. [Experiment and method](https://github.com/ricardodeazambuja/gemma4-26B-only-8B-VRAM/blob/100afff4859b7bccb7adadfc7c5638136ee9f3dc/docs/mtp-benchmark.md)

Our main placement stayed fixed, but prompts, output lengths and cache state
differed. We did not collect interleaved baseline repetitions or synchronized
resource samples. The observed +51.1% must not be advertised as a guaranteed MTP
uplift, a universal advantage over another engine, or an isolated APEX gain.

## Resource accounting

The running target uses **all main GPU layers with CPU MoE weights in the first
27 layers**, six inference/batch threads, **32768 context / one slot**, Q8 target
KV, flash attention, mmap, a CPU vision projector and batch/microbatch 1152.
The service retains **MemoryMax=11 GiB**, no service swap, and **CPUQuota=600%**
(up to six CPU cores' time). These are limits, not measured utilization.

MTP adds the non-QAT Q8 assistant, draft depth **2**, confidence cutoff **0**, Q8
draft KV flags and the default backend draft sampler. It does not reduce main
GPU offload or change the CPU expert-layer count.

| Component observed in the MTP startup log | CPU / host | GPU | Meaning |
|:--|--:|--:|:--|
| Target model buffers | 16,677.49 MiB mapped | 3645.94 MiB | Mapped address-space allocation is not resident RAM |
| Target KV buffers | — | 579.06 MiB | 340.00 + 239.06 MiB |
| Target compute reserve | 103.14 MiB host | 716.73 MiB | Backend reservation |
| Assistant model buffers | 272.00 MiB mapped | 425.34 MiB | Extra model allocations; file size alone misses duplication |
| Assistant compute reserve | 103.10 MiB host; 150.63 MiB CPU reserve also logged | 211.10 MiB | Reservations are not a synchronized peak measurement |
| Assistant KV | Shares target layers 28/29 | Shares target layers 28/29 | No independent full target-sized KV allocation in this run |

The head contributes **636.44 MiB of logged GPU model + compute allocations**,
before treating allocator overhead and shared resources. A startup snapshot showed
**756 MiB free device memory**, including the effects of desktop applications.
It is not a minimum-free-memory measurement during generation. The 11 GiB cgroup
limit includes charged file cache; it is not process RSS. No synchronized CPU,
RAM, power or GPU utilization series was collected for these three requests, so
the report does not invent average load or before/after peak consumption.

## Agent procedure derived from the trials

1. Recover the actual baseline, hardware headroom and user-selected settings.
2. Inspect the main artifact and runtime. Reuse an embedded head or resolve and
   hash-check the matching separate assistant; preserve the target and projector.
3. Budget main/head weights, KV or shared KV, recurrent rollback where applicable,
   compute buffers, paging and application headroom across CPU, RAM and GPU.
4. Add MTP to a candidate with main placement fixed. Inspect separate-head
   placement if needed; record any main-placement change as a different experiment.
5. Verify loading/effective mode, then inspect coherent output before interpreting
   speed. Respect manual testing; never fill the user's slot for a docs task.
6. Compare equivalent workloads when a causal gain is required. Keep the candidate
   if it meets the user's criteria; otherwise restore the saved no-MTP launch.

The operational commands, pinned head recipe, disable path and the unsuccessful
Qwen trial are documented in [MTP operations](../implementations/mtp.md). High draft
acceptance did not prevent the user-reported Qwen repetition regression. We do
not transfer its outcome to Gemma or call a successful startup a quality pass.

## Provenance and reproduction

Local target: [Heretic APEX I-Balanced](https://huggingface.co/mudler/gemma-4-26B-A4B-it-heretic-APEX-GGUF/tree/8e3506b8b11a8ac2d666e0df473fa7ba4ec21497),
file `gemma-4-26B-A4B-heretic-APEX-I-Balanced.gguf`, 19,508,269,920 bytes.
Runtime: [llama.cpp b10883 / `91f6a6cf36138`](https://github.com/ggml-org/llama.cpp/tree/91f6a6cf361385700bbe15981f0f39909df77498),
Vulkan, Linux x86_64. The exact head revision, bytes and verified SHA-256 are in
[the download recipe](../implementations/mtp.md#download-a-compatible-head).

The private log snapshot is 121,652 bytes, SHA-256
`3e982d4b8a5f1db047c8873a7ae686db11059cfcf35752921cdf5b48c876f138`.
Selection used baseline bytes **69734–73158** and MTP bytes **73159–121651**;
three requests have final timing lines. Earlier launches are excluded because
slot/task IDs repeat after restart. Raw prompts, generated text, host paths and
process IDs stay private; [the CSV](gemma4-mtp.csv) contains only numeric timings
and anonymous request labels. Public readers can verify arithmetic, but cannot
independently replay the private prompts or assess their quality from this CSV.

Recompute the published aggregates from the repository root without starting a model:

```bash
python3 - <<'PY'
import csv

with open('docs/benchmarks/gemma4-mtp.csv', newline='') as f:
    rows = list(csv.DictReader(f))
baseline = [r for r in rows if r['phase'] == 'baseline']
mtp = [r for r in rows if r['phase'] == 'mtp']
def rate(group):
    return sum(int(r['output_tokens']) - 1 for r in group) / (
        sum(float(r['decode_ms']) for r in group) / 1000)
gap = 100 * (rate(mtp) / rate(baseline) - 1)
acceptance = 100 * sum(int(r['draft_accepted']) for r in mtp) / sum(
    int(r['draft_generated']) for r in mtp)
assert len(baseline) == 1 and len(mtp) == 2
assert round(rate(baseline), 2) == 9.81
assert round(rate(mtp), 2) == 14.83
assert round(rate([mtp[-1]]), 2) == 15.03
assert round(gap, 1) == 51.1 and round(acceptance, 2) == 56.75
print(f'Baseline {rate(baseline):.2f}; MTP {rate(mtp):.2f} tok/s')
print(f'Observed gap {gap:.1f}%; draft acceptance {acceptance:.2f}%')
PY
```

Evidence limits that remain: only two MTP requests; no matched local A/B; no full
32K input test; no formal quality score; no MTP vision/tool-cycle validation;
external results use different artifacts, hardware and measurement methods.
