# Validate the stack

[Documentation](README.md) · [Measured examples](README.md#resource-use-and-methodology)

Validation follows the requested capability. Separate checks actually run on the user's stack from source inspection, estimates and published benchmarks. UI/visual checks require the user's permission; API, configuration and appropriate nonvisual checks can establish their own narrower results.

When the user reserves inference tests for themselves, prepare the profile and checks without sending generation requests. Report startup, quality and performance as separate results; pending manual feedback is not a pass. For [MTP](implementations/mtp.md), check short-output correctness before long-input or speed tests and include reused-session behavior where required.

## Endpoint and tool protocol

For the example llama.cpp server on the same host:

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/health
curl --fail --silent --show-error http://127.0.0.1:8080/v1/models
```

Use the actual returned ID, URL and authentication for other engines. Repeat from the client environment, not only the host. An OpenShell request that succeeds from the host does not establish sandbox reachability.

This request validates a function-call response shape without executing any tool. It assumes the server alias `localforge-model` from the installation example:

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary '{
    "model": "localforge-model",
    "messages": [{"role": "user", "content": "Call connection_check with marker LOCALFORGE_OK."}],
    "tools": [{"type": "function", "function": {
      "name": "connection_check",
      "description": "Return a connection-test marker.",
      "parameters": {"type": "object", "properties": {
        "marker": {"type": "string"}
      }, "required": ["marker"], "additionalProperties": false}
    }}],
    "tool_choice": {"type": "function", "function": {"name": "connection_check"}},
    "max_tokens": 256,
    "stream": false
  }'
```

Check `choices[].message.tool_calls`, its function name, parseable JSON arguments and marker. If the runtime does not support forced `tool_choice`, record that and test its supported tool selection mode. Do not treat tool-looking prose as a structured call or execute returned text as a shell command.

Next test streaming in the actual client: tool name/arguments can arrive across multiple deltas, and the client must accumulate them correctly. Then run a small disposable-workspace task through the harness: create a harmless file, read it back, process the tool result and give a correct final answer. This proves more than an HTTP tool-schema probe. Preserve tool permissions and keep the test within the requested workspace.

## Required capabilities

| Capability | Check |
|:--|:--|
| Text | Correct template, coherent response, stop/EOS behavior |
| Tools | Structured call, streaming assembly, permitted execution, matching tool-result ID and final answer |
| Reasoning | Selected mode reaches the supported template/API field; reasoning and answer are parsed correctly |
| Context | Representative input near the target window, output reserve, no silent truncation, useful retrieval/reasoning |
| Compaction | Client summarizes at the intended threshold and continues with essential task state |
| Vision | Matching projector/processor, an actual image request and a grounded answer |
| Concurrency | Required simultaneous requests, per-slot context, latency and memory |
| Recovery | Stop/start, reconnect and session continuity where required |

Use a fixed small workload relevant to the user. For derived weights or routing/pruning experiments, compare against the unmodified baseline, including coding/tool tasks and modality checks. Perplexity or a single benchmark is useful additional evidence, not a substitute for the requested capability. Record failed tasks as well as averages.

## Measure resources consistently

Record the hardware, runtime build, weight artifact/hash, launch/client parameters, input length, generated length, concurrency, warm/cold state and observation duration.

- **Latency:** time to first token, prompt processing, decode time and complete task time. Distinguish model work from tools/network/retries.
- **Throughput:** define the engine's token accounting and compute weighted totals when aggregating; do not average unlike rates without explanation.
- **RAM:** process RSS/PSS where available, system available memory and any cgroup usage/limit. File cache and a configured service cap are separate quantities.
- **VRAM:** model-process memory and whole-device use, with other GPU consumers identified. Record snapshots versus sampled peaks.
- **CPU/GPU:** utilization with its normalization and sample interval, temperatures, paging and I/O stalls when relevant.

Measure a short request, the representative task and the requested long-context/concurrency case. Repeat only enough to distinguish noise from the decision at hand. A configured context window does not prove it was filled during the run.

When reading existing llama.cpp b10883 logs, delimit each launch by its saved byte offset or process identity before pairing slot/task timings: task IDs can repeat after restart. Its native decode rate excludes the first output token, so aggregate with `sum(output_tokens - 1) / sum(decode_seconds)` for requests with more than one output token. Keep prompt and total times alongside decode. Count accepted drafts only in the acceptance ratio, never as additional delivered tokens. Preserve final timings and identify cancellations, incomplete requests and the snapshot cutoff. The [sanitized Gemma timing rows](benchmarks/gemma4-mtp.csv) show this accounting.

An MTP comparison needs the same model, hardware/backend, main placement, context, prompt/cache state, sampler and output workload. Interleave repeated baseline/candidate runs when thermal or paging noise matters. Different user requests can establish observed throughput, but their ratio cannot establish a causal MTP gain. Record quality separately; repetitive output can be fast and highly accepted.

## Acceptance and evidence

Promote the candidate only if it meets the required behavior and resource limits. Save exact commands, workload identity, results, failures and known gaps in the local stack record. A generated artifact, a started server, a working API connection and a working autonomous agent are distinct checkpoints.

The existing [RTX 4060 measurements](README.md#resource-use-and-methodology) remain measured examples for their named profiles. Their published comparison rows use different hardware and formats; they are not predicted performance for a fresh installation.
