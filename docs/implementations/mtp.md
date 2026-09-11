# MTP speculative decoding

[Documentation](../README.md) · [Tuning](../llm/tune.md) · [Validation](../validation.md) · [Sources](../sources.md)

Use this guide to download weights, enable, disable, compare or diagnose MTP in an existing stack. It is an
optional inference method, separate from APEX weight quantization and MoE routing.
Keep the selected model and a working launch profile without speculation.

The llama.cpp details below were checked on **September 11, 2026**, against
**b10883**, commit `91f6a6cf361385700bbe15981f0f39909df77498`. Other builds and
architectures require their own source check.

[Operations](#operate-an-existing-stack) · [Head download](#download-a-compatible-head) · [Native flags](#native-configuration) · [Memory](#budget-cpu-ram-and-gpu-together) · [Validation](#validate-and-promote) · [Trial results](#what-our-trials-established) · [Diagnosis](#diagnose-a-regression)

## Operate an existing stack

Start from the saved profile and actual running process. Use native runtime flags
and the service's existing owner; LocalForgeLLM's agent performs these operations.

| Request | Agent action | Completion evidence |
|:--|:--|:--|
| Download additional weights | Identify the missing compatible head, resolve its revision, download that artifact and verify it | Exact path, bytes, SHA-256 and compatibility findings; no restart for a download-only task |
| Enable MTP | Derive a candidate from the working launch, add the required head/options and restart the owned service when idle | Effective speculative mode, unchanged main settings, allocation log and baseline rollback |
| Disable MTP | Restore the saved launch without speculative flags or corresponding environment overrides | Effective mode off and the same target/context/client; retain downloaded weights |
| Compare or repair | Read completed timings and quality feedback; run only the tests the user delegated | Distinguish measured throughput, controlled gain and pending quality checks |

An MTP-only request retains the target's GPU layer count, CPU expert placement,
context, sampling and modalities. Check extra allocations before restarting. If
the head does not fit, inspect supported head placement; explain any necessary
change to the main profile instead of silently reducing its GPU layers. Keep
downloaded, loaded, quality-accepted and speed-measured as separate results in the
[stack record](../agent-workflow.md#keep-a-local-stack-record). A user-requested
trial may stay enabled while their checks are pending; do not label it validated.

## What it does and what it guarantees

An MTP head uses the target model's hidden states to propose a short continuation.
The target verifies proposals together; rejected continuations require state
rollback. Successful drafting can produce several output tokens per target pass.
This does not reduce the main model's parameter count or turn a dense model into
MoE. See the [MTP algorithm overview](https://docs.vllm.ai/projects/speculators/en/latest/user_guide/algorithms/mtp/).

Exact speculative sampling can preserve the target distribution under its
algorithmic assumptions. That is a property of the algorithm, not proof that a
particular quantized backend and state implementation are correct. The
[original paper](https://proceedings.mlr.press/v202/leviathan23a.html) establishes
the algorithmic result; [vLLM's numerical caveats](https://docs.vllm.ai/en/v0.17.0/features/speculative_decoding/#lossless-guarantees-of-speculative-decoding)
explain why batch size and floating-point arithmetic can still change outputs.
Those vLLM checks do not validate llama.cpp.

Distinguish harmless wording differences from corrupted language, repetition,
lost instructions or invalid tool calls. A successful load, nonzero acceptance
or higher tok/s proves none of those quality requirements.

## Check the artifact and implementation

1. Record the target repository, revision, filename/hash, architecture and template.
   Inspect the checkpoint's actual MTP metadata and tensors; a filename ending in
   `-mtp` is insufficient.
2. Identify whether the head is embedded or supplied as a compatible separate
   artifact. Verify the target/head family, QAT/non-QAT variant, hidden dimensions,
   vocabulary/tokenizer and the loader's required tensors.
   A similarly named small model is not automatically an MTP head.
3. Check the installed server's `--version` and `--help`, then trace its loading,
   graph and speculative verification paths. Save the backend and build revision.

For example, the pinned [Qwen3.8 RVN publisher card](https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF/blob/20b94f0613b632b4848bbe3b1e05d9ee0c2b1608/README.md)
describes an embedded Q8 MTP head, approximately 0.42 GiB, after 64 main layers.
Its GGUF architecture identifier is `qwen35`. The separate `mtp-RVN.gguf` is not
needed for those embedded twins. This establishes the publisher's artifact
contract, not local speed or quality.

| Artifact encountered in our work | Consequence |
|:--|:--|
| Qwen3.8 RVN twin with an embedded head | Use the installed head; no duplicate head download is needed |
| Gemma 4 26B-A4B Heretic APEX I-Balanced | Our trial uses a separate non-QAT `gemma4-assistant` head; Q8 refers to this head, while the target stays APEX |
| QAT Gemma target | Discover its matching QAT assistant; do not substitute our non-QAT download recipe by name alone |
| Qwen3.6 APEX target without MTP tensors | Identify a supported complete head or a target bundle containing it; a flag cannot supply missing weights |
| Extracted head tensors alone | Verify that the loader can also obtain embeddings, output normalization and other shared tensors. An inspected 20-tensor Qwen extraction lacked these and was not directly loadable as the separate draft model |

## Download a compatible head

Read the publisher's file inventory at a resolved revision. Obtain expected bytes
and the LFS SHA-256 from the Hugging Face model API (`?blobs=true`), then inspect
GGUF metadata/tensor names against the target and installed loader. Check free
space on the model volume, including any existing partial/cache copy. Do not
download every quant or replace the target to get an optional head.

This is the **specific head downloaded and hash-verified for our Gemma trial**:

| Field | Value |
|:--|:--|
| Repository | [`unsloth/gemma-4-26B-A4B-it-GGUF`](https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/tree/c099eb48e663fd284577b04978a94ffccb261841/MTP) |
| Revision | `c099eb48e663fd284577b04978a94ffccb261841` |
| File | `MTP/mtp-gemma-4-26B-A4B-it-Q8_0.gguf` |
| Bytes / SHA-256 | `461766816` / `6326fb9f5e487aa8dcdd313a091e3c67724cb2a666ec3b7d2895b5b26d93ed1b` |
| Metadata checked | `gemma4-assistant`, 4 layers, embedding width 1024, output width 2816 matching the target |

With the [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli)
installed, choose the stack's model directory and run:

```bash
(
  set -euo pipefail
  MTP_MODEL_DIR=./models
  MTP_REPO=unsloth/gemma-4-26B-A4B-it-GGUF
  MTP_REV=c099eb48e663fd284577b04978a94ffccb261841
  MTP_FILE=MTP/mtp-gemma-4-26B-A4B-it-Q8_0.gguf
  MTP_SHA=6326fb9f5e487aa8dcdd313a091e3c67724cb2a666ec3b7d2895b5b26d93ed1b
  hf download "$MTP_REPO" "$MTP_FILE" \
    --revision "$MTP_REV" --local-dir "$MTP_MODEL_DIR"
  test "$(wc -c < "$MTP_MODEL_DIR/$MTP_FILE")" -eq 461766816
  printf '%s  %s\n' "$MTP_SHA" "$MTP_MODEL_DIR/$MTP_FILE" | sha256sum --check --strict
)
```

Reuse an existing file only after verification; a partial download is not ready.
The CLI preserves the `MTP/` subdirectory. If the stack uses a renamed path,
record that mapping and use the actual path in the launch. A download-only task
ends here. Runtime memory can exceed file size because of duplicated tensors,
compute buffers and KV/state; see [resource accounting](../benchmarks/gemma4-mtp.md#resource-accounting).

Relevant source paths at the pinned llama.cpp revision:

| Path | Inspect for |
|:--|:--|
| [common/arg.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/common/arg.cpp) | Current flag names and parsing |
| [common/common.h](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/common/common.h), [common/common.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/common/common.cpp) | Draft defaults, `load_mtp`, recurrent rollback depth |
| [src/models/qwen35.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/qwen35.cpp) | Required head tensors, main/MTP graphs, architecture-specific loading |
| [src/models/gemma4-assistant.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/gemma4-assistant.cpp), [gemma4.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/gemma4.cpp) | Assistant dimensions/graph and target KV sharing; distinct from the Qwen recurrent path |
| [common/speculative.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/common/speculative.cpp) | Draft context, hidden-state carryover, sampling and acceptance |
| [tools/server/server-context.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/tools/server/server-context.cpp) | Effective activation, target verification, slots and rollback |
| [src/models/delta-net-base.cpp](https://github.com/ggml-org/llama.cpp/blob/91f6a6cf361385700bbe15981f0f39909df77498/src/models/delta-net-base.cpp) | Convolution/recurrent state snapshots for this hybrid family |

## Native configuration

Add MTP options to a **candidate copy** of the existing server command. Keep
sampling, template, context and client settings fixed. This shell fragment assumes
Q8 draft KV has been selected from the supported formats and memory budget:

```bash
mtp_options=(
  --spec-type draft-mtp
  --spec-draft-n-max 1
  --spec-draft-p-min 0
  --spec-draft-type-k q8_0
  --spec-draft-type-v q8_0
)
# LLAMA_SERVER and baseline_options come from the saved launch profile.
"$LLAMA_SERVER" "${baseline_options[@]}" "${mtp_options[@]}"
```

Depth 1 is a small diagnostic starting point, not a quality fix or a universal
optimum. Test deeper drafts only after the candidate gives useful output. The
baseline array must contain no speculative options; release the occupied service
or use a separately budgeted instance before running another model process.

| b10883 option | Meaning |
|:--|:--|
| `--spec-type draft-mtp` | Select native MTP; embedded-head use requires no separate draft model |
| `--spec-draft-n-max N` | Maximum proposed tokens; default 3, with extra work/state as N grows |
| `--spec-draft-n-min N` | Minimum usable draft length; default 0 |
| `--spec-draft-p-min P` | Draft-confidence cutoff; default 0. It is not the target sampler's `--min-p` or a quality guarantee |
| `--spec-draft-type-k`, `--spec-draft-type-v` | Separate draft-context KV types; default F16, not inherited from the target's cache flags |
| `--no-spec-draft-backend-sampling` | Use CPU draft sampling to isolate that component; leaves target verification and model placement in place |
| `--spec-draft-model FILE` | Separate compatible draft artifact, only when required by the chosen workflow |
| `--spec-draft-device`, `--spec-draft-ngl` | Device and GPU layer limits for a separately loaded draft artifact; not independent placement controls for an embedded head |

Old `--draft`/`--draft-max` forms are removed in this build. Do not copy command
lines across releases without checking help. To disable MTP, restore the saved
command without its options: b10883 appends `--spec-type` entries, so adding
`--spec-type none` to an MTP command is not a reliable rollback.

### Gemma trial settings

For our [Gemma launch profile](../README.md#gemma), the candidate adds the following
flags to the existing server command. Set the path to the verified downloaded head:

```bash
mtp_options=(
  --spec-type draft-mtp
  --spec-draft-model ./models/MTP/mtp-gemma-4-26B-A4B-it-Q8_0.gguf
  --spec-draft-n-max 2
  --spec-draft-p-min 0
  --spec-draft-type-k q8_0
  --spec-draft-type-v q8_0
)
```

Pass this array through the stack's saved launcher, as in the native example
above; an array declaration by itself does not start or modify a service. Main
placement stays `--gpu-layers all --n-cpu-moe 27`, with 32768 context, six
threads, Q8 target KV, the CPU projector and the existing 1152 batch sizes.
Depth 2 and confidence cutoff 0 are trial settings, not a universal optimum.
[Unsloth's MTP guide](https://unsloth.ai/docs/models/mtp) also treats draft depth
as a tuning choice. Keep target sampling fixed for the comparison.

### Disable and verify

Wait for the active request to finish, stop the exact service through its owner,
then run the saved baseline without the MTP options. For the documented systemd
Gemma example, the stop command is `systemctl --user stop gemma-apex`; restart
with the original [Gemma command](../README.md#gemma). Restore any service-level
`LLAMA_ARG_SPEC_*` overrides as well. Do not delete the head or alter chat history.

Check health, the actual process arguments, fresh startup logs and `/slots` when
exposed: `speculative` must be `false` after disabling and `true` after enabling.
Use the stack's real endpoint/authentication. Keep the client alias and context
the same. If the user is testing manually, this verification sends no inference
request and leaves output quality pending.

## Budget CPU, RAM and GPU together

For the inspected embedded Qwen path, the main and draft contexts share the loaded
model, while the head and draft KV/compute still cost memory. Separate-draft
device/layer overrides apply when loading a separate artifact; they do not
independently relocate an embedded head. Confirm tensor placement in the log.

Budget these components separately in both RAM and VRAM:

- Main and MTP weights, including tensors shared by both graphs.
- Main KV and recurrent state, plus rollback snapshots needed by speculation.
- Draft KV at its actual context size and precision.
- Main/draft compute buffers, loading transients and other applications.

Our Gemma assistant shared the target's sliding-window/global KV layers. Its
startup still allocated 425.34 MiB of GPU weights and 211.10 MiB of GPU compute,
plus host allocations. Do not add a hypothetical full second KV cache when the
runtime shares it, or assume the head's 0.46 GB file is its complete memory cost.

For this Qwen implementation, speculative depth sets `n_rs_seq`; reducing
`--ctx-checkpoints` does not remove those recurrent rollback snapshots. Draft
context is initialized from the target context size. Increasing context or draft
depth therefore needs a fresh allocation check, not just a head-size estimate.

On a card already near capacity, MTP can displace main weights to CPU. Compare
whole-layer offload and supported dense-FFN/MoE placement using
[the tuning guide](../llm/tune.md). RAM capacity can make a placement feasible;
memory bandwidth, quantized kernels and synchronization determine its speed.

For the inspected embedded Qwen with head block 64, the candidate override
`--override-tensor 'blk\.64\..*=CPU'` moved that block's weights to the CPU
while retaining 41 main GPU layers. This is architecture-specific: never copy
the block number to Gemma or another model. It did not move all draft KV/compute
off GPU and did not resolve the reported Qwen quality regression.

Keep two comparisons distinct: same-placement MTP off/on isolates speculation;
best feasible placement for each mode compares deployable configurations. If
placement changes, report that confound rather than attributing all change to MTP.

## Validate and promote

Respect who is running tests. If the user reserved inference testing for
themselves, prepare the profile and acceptance criteria; leave quality and speed
pending. Do not fill their only slot with an unattended long-context benchmark.

1. Save baseline commands and current service state. Check that the slot is idle
   before a restart. Load the candidate and inspect both contexts, allocation
   headroom, initialization warnings and the effective speculative mode.
2. Use a short representative request first, with an explicit output cap and
   deadline. Check coherent language, system instructions, stop behavior and
   required structured output. Repetition or corrupted output rejects the candidate.
3. Compare equivalent requests under fixed settings. A greedy/seed-controlled
   pair helps locate divergence; textual identity alone is neither a broad quality
   score nor a prerequisite for semantically valid stochastic outputs.
4. Check a fresh process and reused sessions, including cancellation/retry and tool
   turns when required. Test the representative long input only after short
   correctness passes. Allocating 32K does not establish quality on 32K input.
5. Record native prompt/decode timings, output length, latency, draft attempts and
   accepted draft tokens, plus RAM/VRAM observations. Report acceptance with its
   numerator and denominator; exclude draft attempts from delivered token counts.
6. Promote only after the requested quality, speed and resource limits pass.
   Otherwise restore the baseline and retain the rejected profile and evidence.

A cancelled stream without final timings is not an exact throughput measurement.
High acceptance can coexist with slower generation because drafting, verification
and rollback cost time. The RVN publisher's full-GPU benchmarks on two RTX PRO
6000 cards include both gains and regressions; they are not predictions for a
desktop with CPU offload. See [the measured methodology](../validation.md#measure-resources-consistently).

## What our trials established

- **Gemma:** two user requests with final timings measured **14.83 tok/s weighted
  decode**; the longer response logged **1535 output tokens in 102.05 seconds**
  of decode, **15.03 tok/s** under the engine's first-token accounting. The nearby
  no-MTP request was 9.81 tok/s. Their **+51.1% observed gap is not a controlled
  MTP gain**: the requests differed. Configured context was 32K; the largest
  logged live context was 2265 tokens. Formal quality evaluation remains pending.
- **Qwen3.8 RVN:** reducing main GPU layers from 41 to 33 confounded the first
  comparison. Retaining 41 with a GPU head failed allocation; moving only the
  head weights to CPU loaded, but the user again reported duplicated/degraded
  output. Startup therefore did not establish a usable configuration. The exact
  cause of the quality regression was not established.

See [timings, external comparisons and resource definitions](../benchmarks/gemma4-mtp.md).
An independent [Gemma MTP experiment](https://github.com/ricardodeazambuja/gemma4-26B-only-8B-VRAM/blob/100afff4859b7bccb7adadfc7c5638136ee9f3dc/docs/mtp-benchmark.md)
also reports repetition at positive draft-confidence cutoffs with sampling.
That supports checking this setting; it does not prove the cause of our Qwen
incident or make cutoff 0 a universal correctness guarantee.

## Diagnose a regression

| Observation | Discriminating check |
|:--|:--|
| Coherent but slower | Compare placement, completed native timings, accepted tokens per draft round, CPU paging and memory pressure |
| Broken language or loops on the first request | Compare MTP off/on at the same placement and request settings; inspect verification/backend and recurrent rollback paths |
| First request works, later history/tool turns fail | Compare fresh versus reused process/slot, cancellation and restored prompt state |
| Server is healthy but MTP is inactive | Inspect initialization warnings and effective slot state; accepted CLI flags are insufficient |
| Failure after increasing context/depth | Inspect both contexts, rollback-state allocation and headroom before another generation |

Use one diagnostic change at a time. CPU draft sampling isolates sampling;
draft depth, KV precision and flash attention change other paths. Lower precision,
repetition penalties or a different system prompt should not conceal a newly
introduced inference regression. Preserve malformed examples locally, keeping
private prompts and machine paths out of public documentation.

### Upstream evidence as of September 11, 2026

| Primary source | Evidence and limits |
|:--|:--|
| [Issue #25618](https://github.com/ggml-org/llama.cpp/issues/25618) | Open reports of speculative/ordinary decode divergence on quantized targets, including Qwen. Some differences are semantically harmless. Later reports also cover CUDA; switching backend alone is no guarantee |
| [Issue #27296](https://github.com/ggml-org/llama.cpp/issues/27296) | Open Qwen MTP reports of corrupted output after long/short or tool turns. The repeated-request trigger does not by itself explain a fresh-process failure |
| [PR #26358](https://github.com/ggml-org/llama.cpp/pull/26358) | Proposed Vulkan FA packing change, closed without merge; author expressed uncertainty. Do not present it as an accepted fix |
| [PR #28488](https://github.com/ggml-org/llama.cpp/pull/28488) | Open draft with batch-invariance tests; reproduction work, not a released repair |
| [PR #27173](https://github.com/ggml-org/llama.cpp/pull/27173) | Open change combining speculative performance work and a recurrent snapshot correction. Not a released universal remedy |
| [PR #28705](https://github.com/ggml-org/llama.cpp/pull/28705) | Merged Vulkan ARGSORT race/bounds fixes, released in b10903. This alone does not establish an MTP fix: the inspected MTP top-k sampler dispatches a separate TOP_K operation |

Read issue corrections and actual merge status, then check whether the affected
code is in the installed execution path. These reports justify investigation;
they do not identify the cause of every local loop. F16 KV, depth 1 and a newer
release must pass the same workload before being called fixes.
