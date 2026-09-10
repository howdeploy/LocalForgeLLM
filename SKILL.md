---
name: localforgellm
description: Build, tune, update and repair local LLM stacks for the user's hardware, including MoE models, inference engines, weight processing and agent interfaces. Use for local model installation, performance or context tuning, derived model builds, and connecting Pi, OpenShell, llama UI or Hermes. Generative image, video and audio workflows are a planned branch.
---

# LocalForgeLLM

Turn the user's request into a working, reproducible local AI stack. Select the model, engine, weight format and interface together; measure the result on the intended workload. Use existing implementations and their native configuration before writing a custom integration.

This skill belongs to the complete LocalForgeLLM repository. Resolve the links below relative to this file. Keep `docs/` with the skill; copying this file alone loses its operational references. Agents that read `AGENTS.md` discover this entry automatically; in other clients, explicitly ask the agent to read this file. Native skill registration depends on the host agent's discovery rules.

## Choose the work

| Request | Route | Result |
|:--|:--|:--|
| Install a model or build a stack for a task | [Level 1](docs/llm/install.md) | Compatible dependencies, weights, server and working client |
| Change context, memory, speed or model behavior | [Level 2](docs/llm/tune.md) | Measured configuration or a separately identified model modification |
| Create a custom model from full weights | [Level 3](docs/llm/build.md) | Derived artifact with source revision, recipe and quality results |
| Update, resume, repair or replace a component | [Operations](docs/operations.md) | Working stack with a tested rollback path |
| Connect an agent or customize its shell | [Interfaces](docs/interfaces/README.md) | Working client/harness connection and the requested extension |
| Image, video or audio generation | [Generative branch](docs/generative/README.md) | Explain planned status; do not claim an implemented workflow |

Levels describe the nature of the task, not mandatory steps. Installing a published quant does not require building one. A tuning task may move into level 3 when it needs different weights; explain the additional compute, storage and artifact changes before that work.

## Execute

1. Read [architecture](docs/architecture.md) and [agent workflow](docs/agent-workflow.md). Extract the task, capabilities, existing choices, hardware limits and intended interface. Ask only for missing information that changes the result; inspect discoverable machine state yourself.
2. Find an existing stack record and verify its processes, paths, versions and endpoint. Preserve the working baseline. On a new machine, inventory hardware before selecting an implementation.
3. Read the relevant level guide, [engine selection](docs/implementations/engines.md), and the selected model/runtime's own documentation. Verify exact architecture, checkpoint format, backend, context, template and tool-call support. The catalog is a starting point, not a closed compatibility list.
4. Perform the requested work. Save concrete commands, dependency versions and effective settings in the stack's local record. Use isolated environments and a candidate output/profile when replacing something that already works.
5. Follow [validation](docs/validation.md): check the endpoint, requested capabilities, actual client tool cycle, speed, memory and the target context. A plain chat response does not prove a coding agent works.
6. Promote the candidate after it meets the user's criteria. Record the result and rollback procedure. Give the user the exact start/stop/connect instructions and measured limits.

## Keep the distinctions

- The coding agent orchestrates; the inference engine executes the model; the harness owns tools and history; OpenShell owns its execution environment and access rules.
- APEX selects precision for weights. It is optional, is not an agent harness and is not a runtime optimizer. Read [APEX](docs/implementations/apex.md) only when using that method.
- CPU/GPU placement does not change the number of experts selected by the learned router. Changing routing, pruning tensors and changing tensor precision have different compatibility and quality implications.
- Advertised model context, server context per slot, client context and output budget must agree. Cumulative session tokens are not the current context size.
- “Build from scratch” in level 3 means constructing a derived deployment artifact from existing full weights. Training a new base model requires a separate explicit training task, data and compute plan.
- Completion means a working result for the requested workload. Report source-inspected, estimated and measured facts separately. Never borrow benchmark speed or memory from another machine as a local result.

## Extend and maintain

For an unfamiliar implementation, use [Learn an implementation](docs/agent-workflow.md#learn-an-implementation). For custom interfaces, use the code maps in [Pi](docs/interfaces/pi.md), [OpenShell](docs/interfaces/openshell.md), [llama UI](docs/interfaces/llama-ui.md) and [Hermes](docs/interfaces/hermes.md). Read the actual checkout before changing it; versions can change both configuration and architecture.

Keep model files, raw sessions and credentials local. A task to configure a stack does not itself authorize publishing weights, renting GPUs, changing unrelated global providers, deleting sandbox volumes or weakening access policy. Continue all already-authorized work and request only the additional decision actually needed.
