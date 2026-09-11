---
name: localforgellm
description: Choose local LLM models and quantizations for the user's real hardware and target tokens per second; compare CPU/RAM/GPU placement. Build, tune, update and repair dense or MoE stacks, process weights, and connect Pi, OpenShell, llama UI or Hermes. Use for model recommendations, memory/speed feasibility, installation, context tuning and MTP head downloads or switching. Generative image, video and audio workflows are a planned branch.
---

# LocalForgeLLM

Turn the user's request into a working, reproducible local AI stack. Select the model, engine, weight format and interface together; measure the result on the intended workload. Use existing implementations and their native configuration before writing a custom integration.

This skill belongs to the complete LocalForgeLLM repository. Resolve the links below relative to this file. Keep `docs/` with the skill; copying this file alone loses its operational references. Project `AGENTS.md` directs agents here. For discovery outside this checkout, follow [native skill registration](docs/agent-workflow.md#register-the-skill).

## Choose the work

| Request | Route | Result |
|:--|:--|:--|
| Recommend a model/quant or assess a target tok/s | [Candidate comparison](docs/agent-workflow.md#select-a-candidate) → [Level 2](docs/llm/tune.md) | Hardware/resource budget and compared placements; measured speed or an explicit estimate with a validation step |
| Install a model or build a stack for a task | [Level 1](docs/llm/install.md) | Compatible dependencies, weights, server and working client |
| Change context, memory, speed or model behavior | [Level 2](docs/llm/tune.md) | Measured configuration or a separately identified model modification |
| Download MTP weights; enable, disable or diagnose speculation | [MTP operations](docs/implementations/mtp.md#operate-an-existing-stack) | Verified compatible head when needed, preserved main placement, effective mode and a working rollback |
| Create a custom model from full weights | [Level 3](docs/llm/build.md) | Derived artifact with source revision, recipe and quality results |
| Update, resume, repair or replace a component | [Operations](docs/operations.md) | Working stack with a tested rollback path |
| Connect an agent or customize its shell | [Interfaces](docs/interfaces/README.md) | Working client/harness connection and the requested extension |
| Image, video or audio generation | [Generative branch](docs/generative/README.md) | Explain planned status; do not claim an implemented workflow |

Levels describe the nature of the task, not mandatory steps. Installing a published quant does not require building one. A tuning task may move into level 3 when it needs different weights; explain the additional compute, storage and artifact changes before that work.

## Execute

1. Read [architecture](docs/architecture.md) and [agent workflow](docs/agent-workflow.md). Extract the task, capabilities, existing choices, hardware limits and intended interface. Ask only for missing information that changes the result; inspect discoverable machine state yourself.
2. Find an existing stack record and verify its processes, paths, versions and endpoint, including stacks outside this checkout. Identify whether process/device inspection sees the host or only a sandbox. Preserve the working baseline and inventory actual available resources before selecting an implementation.
3. Read the relevant level guide, [engine selection](docs/implementations/engines.md), and the selected model/runtime's own documentation. Verify exact architecture, checkpoint format, backend, context, template and tool-call support. The catalog is a starting point, not a closed compatibility list.
   For a model/quant or speed decision, compare concrete CPU/GPU placements and compatible candidates against the existing measurements. Budget weights, KV/recurrent state, buffers and application headroom in both RAM and VRAM. A GGUF larger than VRAM is a placement problem to investigate, not a reason by itself to reject it or select the smallest quant. Keep the user's selected model/version fixed unless they agree to a replacement.
4. Perform the requested work. Save concrete commands, dependency versions and effective settings in the stack's local record. Use isolated environments and a candidate output/profile when replacing something that already works.
5. Follow [validation](docs/validation.md): check the endpoint, requested capabilities, actual client tool cycle, speed, memory and the target context. A plain chat response does not prove a coding agent works.
6. Promote the candidate after it meets the user's criteria. Record the result and rollback procedure. Give the user the exact start/stop/connect instructions and measured limits.

## Keep the distinctions

- The coding agent orchestrates; the inference engine executes the model; the harness owns tools and history; OpenShell owns its execution environment and access rules.
- APEX selects precision for weights. It is optional, is not an agent harness and is not a runtime optimizer. Read [APEX](docs/implementations/apex.md) only when using that method.
- MTP drafts tokens for target verification. Follow [MTP operations](docs/implementations/mtp.md#operate-an-existing-stack) to discover/download only a missing compatible head and switch the saved profile on or off. Preserve the main model's layers, CPU expert placement and context for an MTP-only request. A loaded head or high acceptance does not establish useful output or a speed gain; keep manual quality checks pending until the user's feedback. See the [Gemma case study](docs/benchmarks/gemma4-mtp.md) for measured results and their limits.
- CPU/GPU placement does not change the number of experts selected by the learned router. Changing routing, pruning tensors and changing tensor precision have different compatibility and quality implications.
- Advertised model context, server context per slot, client context and output budget must agree. Cumulative session tokens are not the current context size.
- “Build from scratch” in level 3 means constructing a derived deployment artifact from existing full weights. Training a new base model requires a separate explicit training task, data and compute plan.
- Completion means a working result for the requested workload. Report source-inspected, estimated and measured facts separately. Never borrow benchmark speed or memory from another machine as a local result.
- An advice-only request can end with a comparative assessment and clearly identified unknowns. A required speed is verified only by local measurements at a stated context and workload; file size, an accepted flag or another model's result cannot establish it.

## Extend and maintain

For an unfamiliar implementation, use [Learn an implementation](docs/agent-workflow.md#learn-an-implementation). For custom interfaces, use the code maps in [Pi](docs/interfaces/pi.md), [OpenShell](docs/interfaces/openshell.md), [llama UI](docs/interfaces/llama-ui.md) and [Hermes](docs/interfaces/hermes.md). Read the actual checkout before changing it; versions can change both configuration and architecture.

Keep model files, raw sessions and credentials local. A task to configure a stack does not itself authorize publishing weights, renting GPUs, changing unrelated global providers, deleting sandbox volumes or weakening access policy. Continue all already-authorized work and request only the additional decision actually needed.
