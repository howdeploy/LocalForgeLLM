# Generative models — planned

[Documentation](../README.md) · [Architecture](../architecture.md)

This branch is reserved for image, video and audio generation. Its installation, tuning and model-building workflows are planned and are not implemented in this framework yet.

The intended structure follows the LLM branch: install an existing model and stack; adapt its execution/settings; build a derived artifact using established weight-processing implementations. Model families, engines, graph formats and validation procedures will be specified when this branch is developed.

When a user requests generative work, explain this status. Do not present LLM quantization recipes, APEX support or llama.cpp settings as a supported image/video pipeline. A request to implement the branch is a framework-development task with its own concrete model, engine, workflow and acceptance criteria.

An LLM reading an image through a vision projector remains part of the [LLM branch](../llm/install.md).
