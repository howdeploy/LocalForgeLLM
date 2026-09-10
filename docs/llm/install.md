# Level 1 — install a model and its stack

[Documentation](../README.md) · [Engine selection](../implementations/engines.md)

The output is a usable model, runtime, dependency environment and client connection, with a saved launch profile. Downloading an existing quantized artifact is sufficient when it meets the task; a quantizer is not an installation dependency for that artifact.

## Inventory the target machine

On Linux, these read-only commands provide a starting inventory; use the OS equivalents elsewhere:

```bash
uname -sm
cat /etc/os-release
lscpu
free -h
df -h .
```

For NVIDIA, inspect `nvidia-smi`; for a Vulkan build, inspect `vulkaninfo --summary` if installed. Use the selected runtime's device-list command to confirm the device order. Check disk space on the actual model volume, existing listeners, running model services and other memory consumers. On Apple Silicon account for shared system/GPU memory rather than adding them as independent capacities.

Keep headroom for the OS, desktop and user workloads. MoE active parameters estimate computation, not the complete weight-storage requirement. Disk-resident experts still need an engine that supports streaming/offloading; “fits on SSD” alone does not establish a usable stack.

## Match model, format and runtime

Read the source model's card, architecture config and deployment notes, then the selected [engine's](../implementations/engines.md) support matrix. Verify:

- Exact architecture and revision, tokenizer and chat template.
- Weight format supported by that engine and device backend.
- Required modalities, projector/adapters and tool-call/reasoning parsers.
- Native context, engine context support and the requested output budget.
- Download size, runtime memory, scratch/build space and compatibility requirements.

A model family name or `.gguf` extension does not prove that an older binary implements the architecture. Choose a supported binary/checkpoint combination. Preserve model license and attribution metadata when downloading or later deriving artifacts.

## Install the dependencies that this engine requires

Prefer an official prebuilt release when it supports the target. Record its tag and checksum. Otherwise use a pinned source checkout and the upstream build instructions. Keep different candidate engines/builds in separate environments.

For llama.cpp, the [build guide](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/docs/build.md) covers CPU, CUDA, Vulkan, Metal and other backends. Select one appropriate backend; do not install every GPU toolkit. A Vulkan build needs Vulkan development libraries and a shader compiler; CUDA needs a compatible toolkit/driver; binary archives have their own runtime-library requirements.

Example source build, run inside a checked-out llama.cpp revision after satisfying its Vulkan requirements:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build build --config Release --target llama-server -j 4
./build/bin/llama-server --version
./build/bin/llama-server --list-devices
```

The four build jobs are an example, not a CPU tuning result. Choose a suitable build concurrency for the machine. For Python engines, use a dedicated virtual environment and the engine's pinned requirements. For containers, record the image digest, device access and mounted model paths. A container does not install the host's GPU driver.

## Download only the selected artifacts

Resolve a model repository revision and exact filenames before a large download. Obtain every required shard and matching multimodal artifact. Avoid downloading all published quantization variants.

With the official [Hugging Face CLI](https://huggingface.co/docs/huggingface_hub/guides/cli), a single selected file can be downloaded as follows; set these variables from the resolved manifest:

```bash
hf download "$MODEL_REPO" "$MODEL_FILENAME" \
  --revision "$MODEL_REVISION" --local-dir "$MODEL_DIR"
```

Verify file size/completion and record the SHA-256. Preserve original artifact names in the record. A renamed local file needs an explicit mapping to its source. Do not infer projector compatibility from similar names.

## Start a baseline and connect it

For a compatible GGUF and llama.cpp build, this is a small initial launch, not a tuned recommendation for every model:

```bash
llama-server --model "$MODEL_FILE" --alias localforge-model \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 8192 --parallel 1 --fit on
```

Check `--help` for the actual binary and read the loading log. Confirm devices, effective context and memory allocation. Automatic fitting is a useful starting point; it is not a quality/performance search or a guarantee that the whole PC has enough free RAM.

Use `/v1/models` to discover the actual API model ID. For a client on the same host, the base URL is `http://127.0.0.1:8080/v1`. A sandbox, VM or remote client needs its own reachable address; follow [interfaces](../interfaces/README.md).

Run [validation](../validation.md), then save the launch and client configuration in the [stack record](../agent-workflow.md#keep-a-local-stack-record). Tune only the constraints that need improvement through [level 2](tune.md). Our complete [Qwen/Gemma examples](../README.md#launch-profiles) illustrate one tested machine and remain optional.
