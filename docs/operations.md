# Updates, repair and resumption

[Documentation](README.md) · [Stack record](agent-workflow.md#keep-a-local-stack-record)

## Inspect before changing

Recover the user's stack record, active process/service, model files and client settings. Check actual versions and effective endpoints against the record. Identify the smallest relevant component: model artifact, engine, backend, client, harness, execution environment or interface.

For a context adjustment, follow [tuning](llm/tune.md). For a new quantization, follow [building](llm/build.md). Updating an interface should not automatically replace the model or its launch profile.

For MTP downloads or switching, use [MTP operations](implementations/mtp.md#operate-an-existing-stack). Enable a candidate derived from the saved baseline; disable by restoring the command without speculative options. Preserve the main model, placement, context and client mapping. Verify the effective mode after the owned service restarts; a startup check is separate from the user's quality and speed tests.

## Update with a recoverable candidate

1. Save the working launch/client configuration and identify the current binaries, model hashes and service ownership. Back up persistent state before migrations that alter it.
2. Read upstream release notes and configuration migrations between installed and candidate revisions. Check architecture, API, model-template, backend and stored-session compatibility.
3. Install/build the candidate separately. Keep the working artifact and environment until the replacement passes. Avoid an unbounded upgrade of every package in the user's global environment.
4. Validate the candidate with the saved workload. Use a separate endpoint when resources permit. If two models cannot coexist in memory, arrange a controlled stop/test/restart of the owned service with the baseline ready.
5. Switch the intended clients, verify their effective provider/model/context, and test resumption of a real client session when it is part of the task.
6. Record the accepted version and exact rollback. Removing old artifacts is a separate cleanup decision when it would delete the only recovery copy or user data.

An upstream upgrade can change deployment architecture. In particular, current OpenShell source has removed the managed inference route used in our `0.0.110` setup; follow the version-specific [OpenShell guide](interfaces/openshell.md), including persistent-volume handling. Do not apply the migration by deleting an existing user's sandbox during a routine update.

## Diagnose by layer

| Symptom | First discriminating check | Likely next action |
|:--|:--|:--|
| Server fails before loading | Binary dependencies, driver/backend, architecture support, logs | Correct the matching dependency/build |
| OOM during load | Weight placement, available RAM/VRAM, other processes | Adjust placement/format or choose a fitting candidate |
| OOM only with long input | Effective context, KV/state, batches and concurrent slots | Rebalance the runtime and client context budget |
| Host curl works; agent gets 503/DNS failure | Request from the actual sandbox/VM and its network path | Fix the scoped route/profile or host reachability |
| Chat works; tools fail | Template, tool parser, structured `tool_calls`, replay and executor | Correct the client/runtime capability mismatch |
| Settings appear ignored | Actual process command and outgoing request | Resolve client overrides, stale process or wrong provider |
| Context error despite compaction | Server per-slot context, client limit, output/tool reserve | Align limits and test the compaction path |
| High decode but slow task completion | Prompt processing, tool time, retries and cache behavior | Tune the bottleneck measured in the real workload |
| Update breaks only old sessions | Session schema, compaction state, tool-call history | Follow migration or test a new session without discarding history |

Stop services through their owning manager and exact identity. Do not use broad process killing against all model or agent processes. In OpenShell, stopping and deleting a sandbox have different data consequences; preserve the volume unless deletion is explicitly part of the task.

## Rollback and interruption

Rollback restores the previous artifact, executable/environment, launch parameters and client mapping together. Restoring only a binary can leave an incompatible client configuration or migrated database. Verify the old endpoint and workload after reverting the candidate.

After interruption, inspect partial downloads/builds, checksums, exit status and logs. Resume only a stage supported by the underlying tool's resume semantics. Record completed stages, remaining work and the last known-good profile; do not mark a partial output as ready.
