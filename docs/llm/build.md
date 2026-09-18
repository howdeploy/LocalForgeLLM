# Level 3 — build a derived model from full weights

[Documentation](../README.md) · [APEX recipe](../implementations/apex.md) · [Recorded REAP → APEX build](../implementations/reap.md)

Here “create a model from scratch” means constructing a new deployment artifact from existing full model weights: convert, calibrate, allocate precision, quantize, or apply another supported transformation. Reuse existing implementations and compose their stages. Training a new base model from random initialization is a separate task with a dataset, training recipe and compute budget.

## Plan the artifact lineage

Record the parent model repository and revision, full-weight dtype, architecture, tokenizer, chat template and optional projectors/adapters. Choose the target engine/format first. A GGUF conversion is useful for a GGUF runtime; it is not an intermediate that every other engine needs.

Estimate storage for downloads, conversion output, calibration artifacts, candidate outputs and temporary files together. As a scale check, 35 billion parameters at two bytes each is roughly 70 GB decimal for tensors alone; sharding and metadata affect exact sizes. Check actual manifests rather than promising a fixed free-space threshold.

Distinguish three resource profiles:

- **Recipe editing:** small text/configuration changes; ordinary desktop hardware is sufficient.
- **Conversion and quantization:** can be CPU/SSD/RAM work; memory behavior depends on the actual converter and tensor sizes.
- **Calibration and evaluation:** execute the model on data; often the heavier stage, especially with full weights.

Use local compute when it meets the plan. If rental is needed, prepare the exact job, input/output sizes and recovery/download plan before requesting the additional spending decision. Do not infer runtime, cost or peak RAM from GPU model alone.

## A GGUF build path

Use a pinned llama.cpp checkout, its converter dependencies in a dedicated environment, and full F16/BF16/FP32 source weights. Match tokenizer/config files to the same revision. The [conversion and quantization guide](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/quantize/README.md) is the starting point; some architectures require a newer Transformers version than the default converter environment.

From the checkout root, install the converter requirements in the activated dedicated Python environment with `python -m pip install -r requirements.txt`. Resolve any architecture-specific dependency adjustment to a recorded version. If the existing CMake build only contains the server, build the quantizer with `cmake --build build --config Release --target llama-quantize -j 4`. When calibration is part of the task, also build `llama-imatrix` through the same command with that target. A fresh checkout first needs the backend configuration from [installation](install.md#install-the-dependencies-that-this-engine-requires).

Run from the converter checkout, with `SOURCE_DIR` and `BUILD_DIR` set to the selected source and a separate output directory:

```bash
python convert_hf_to_gguf.py "$SOURCE_DIR" \
  --outfile "$BUILD_DIR/model-bf16.gguf" --outtype bf16

./build/bin/llama-quantize \
  "$BUILD_DIR/model-bf16.gguf" "$BUILD_DIR/model-Q4_K_M.gguf" Q4_K_M
```

BF16 and Q4_K_M are examples. Select a supported source/output dtype and quantization for the actual architecture/backend. For split inputs/outputs, use the converter/quantizer's documented shard handling. Convert multimodal components separately as required; converting only language tensors does not preserve working vision automatically.

Load and check the converted baseline before comparing lossy transforms when resources permit. Do not silently requantize an already low-bit artifact as a substitute for full weights. That adds loss and changes the experiment.

## Calibration and custom precision

Use representative calibration data for the intended workload and record its identity, preprocessing, seed/settings and model revision. Keep evaluation inputs separate where feasible. A calibration file for another model or incompatible tensor layout is not interchangeable merely because the architectures resemble each other.

For llama.cpp, inspect [imatrix](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/imatrix/README.md) and the built tool's help. A schematic command, after choosing a fitting execution configuration, is:

```bash
llama-imatrix -m "$BUILD_DIR/model-bf16.gguf" \
  -f "$CALIBRATION_TEXT" -o "$BUILD_DIR/imatrix.gguf"
```

Add the verified context/device/offload parameters for the calibration machine. The extension does not make old imatrix formats compatible with newer tools; use a matching producer/consumer version.

Apply the matrix with the quantizer's `--imatrix` option. For per-tensor precision, use a reviewed tensor-type file or the [APEX generator](../implementations/apex.md). For other formats/methods, follow their calibration and export contract instead.

The inspected quantizer supports `--max-buffer-size MiB` to bound the tensor-row quantization buffer. This is not a process-wide RAM cap; mappings, calibration data, outputs and other allocations still matter. If the APEX wrapper does not expose this option, invoke `llama-quantize` directly with the same reviewed tensor file. See [the actual CLI parser](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/quantize/quantize.cpp).

## Other transformations

For the tools used in our rented-server Gemma rebuild, follow [REAP, APEX and expert caching](../implementations/reap.md): pinned full weights, architecture-specific REAP observation/pruning, BF16 conversion, fresh imatrix, exact tensor precision and held-out checks. The recorded 2.81% smaller GGUF is a storage result; the separate expert-cache gain comes from runtime placement. Gemma 4 required a local adapter at the inspected REAP revision.

An adapter merge, expert/layer pruning pass, distillation or fine-tuning task needs its own implementation, data requirements and evaluation. Some require training; some are deterministic transforms. Use the user's requested operation and the [implementation discovery procedure](../agent-workflow.md#learn-an-implementation), and preserve architecture/tokenizer/adapter compatibility. Do not describe a metadata edit as a trained or distilled model.

## Validate, package and reuse

Keep the original weights immutable. Give every candidate a unique output path, record checksums and save the exact recipe/tool revision. Check tensor/metadata integrity, loading, tokenizer/template behavior, required modalities and tools, then compare [quality and resources](../validation.md) against the baseline.

The output package consists of the artifact files, required tokenizer/projector/adapters, provenance, recipe, calibration identity, license/attribution and measured results. Store it locally first. Publishing to a model hub is a separate explicit action; do not upload private prompts, calibration data or credentials with the artifact.

Finally serve the selected artifact through [level 1](install.md), tune the deployment through [level 2](tune.md), and update the stack record. A successful quantization process is not yet a usable agent stack.
