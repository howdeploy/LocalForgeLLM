# Working in LocalForgeLLM

LocalForgeLLM is an agent-operated framework for building, adapting and maintaining local AI stacks. The agent selects implementations for the user's task and hardware. APEX is one weight-processing method; llama.cpp, FreeToken and other engines are replaceable components.

For a stack task, read [SKILL.md](SKILL.md), then follow the relevant guides in [docs/README.md](docs/README.md). Classify the task before choosing a model or engine:

- **LLM / level 1:** install an existing model, its runtime and dependencies.
- **LLM / level 2:** tune an existing stack; modify model behavior or internals when the task requires it and the implementation supports it.
- **LLM / level 3:** build a derived model artifact from full weights using existing conversion, calibration and weight-processing tools.
- **Generative models:** planned branch; read [the placeholder](docs/generative/README.md) and state its current status.

Start an existing stack task from its saved profile and actual running state. Preserve the user's model, interfaces, data and permissions unless their request changes them. A new model or engine must be understood through its own versioned documentation and source, using [the discovery procedure](docs/agent-workflow.md#learn-an-implementation).

For framework development, maintain the skill, documentation routes, examples and source references together. Keep machine-specific state, credentials and weights out of Git. Documentation work does not require launching models or changing a user's running stack. Report what was actually checked.
