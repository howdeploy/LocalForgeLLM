# APEX — one weight-processing implementation

[Documentation](../README.md) · [Level 3](../llm/build.md) · [Tested deployment examples](../README.md#launch-profiles)

APEX creates mixed-precision recipes for GGUF tensors. It can assign different precision to expert, shared-expert, attention and layer groups, then call llama.cpp's quantizer. Our Qwen/Gemma runs use published APEX artifacts; the framework also supports other methods selected for the task.

## What can be changed on a desktop

| Operation | Work required |
|:--|:--|
| Edit a precision recipe | Small text/configuration operation |
| Apply the recipe to full weights | Quantizer execution, CPU/RAM/SSD and a new output artifact |
| Generate an importance matrix | Model inference over calibration data |
| Change context or CPU/GPU placement of an existing APEX GGUF | Ordinary runtime tuning; no APEX rebuild |
| Change active expert count, router or tensor topology | Architecture-specific model modification; not an APEX precision setting |

On a 4060-class PC, recipe editing is straightforward and CPU quantization can be feasible with sufficient storage and an appropriate buffer budget. Full-weight calibration and quality evaluation have different memory/compute requirements. We have not measured a complete local custom-APEX build's duration or peak RAM.

## Use the actual scripts

The inspected [generator](https://github.com/localai-org/apex-quant/blob/636cec7e3f8d308e4162ab2bd5ec4b56807dd806/scripts/generate_config.sh) writes a text file for `llama-quantize --tensor-type-file`. It is not a JSON launch configuration.

Set `APEX_DIR` to the pinned checkout and `BUILD_DIR` to a separate output directory. This 40-layer example must be adapted to the model's actual layer count and tensor names:

```bash
bash "$APEX_DIR/scripts/generate_config.sh" \
  --profile compact --layers 40 -o "$BUILD_DIR/tensor-types.txt"
```

A custom allocation can be generated without loading any model:

```bash
bash "$APEX_DIR/scripts/generate_config.sh" \
  --custom --layers 40 \
  --edge-exp Q5_K --near-exp Q4_K --mid-exp Q3_K \
  --edge-shared Q6_K --mid-shared Q6_K \
  --edge-attn Q6_K --mid-attn Q4_K \
  -o "$BUILD_DIR/tensor-types-custom.txt"
```

These precisions illustrate the controls, not an evaluated recommendation. The generator defaults to 40 layers; always supply the actual count. Its `--dense-layers` describes leading dense FFN layers within a MoE, while `--arch dense` selects a fully dense architecture. They are different modes and cannot be combined in this version.

## Inspect the emitted rules

Rules are tensor-name patterns followed by a quantization type. Check them against the converted GGUF's real tensor inventory. Architecture-specific names, missing groups and broad regex matches can make a plausible recipe behave differently from its label.

For a hand-edited exact-tensor rule, anchor and escape the pattern, for example:

```text
^blk\.0\.ffn_down_exps\.weight$=Q5_K
```

Confirm the tensor exists before using this example. The inspected quantizer applies regex matching and precedence; check rule ordering and actual output tensor types. A rule that matches nothing does not establish protection for the intended component. Keep router/normalization-sensitive tensors at an appropriate supported precision based on the architecture and quality results, not a copied rule for another family.

## Produce a new artifact

The [wrapper parser](https://github.com/localai-org/apex-quant/blob/636cec7e3f8d308e4162ab2bd5ec4b56807dd806/scripts/quantize.sh) accepts `--profile`, `--config`, `--imatrix`, `--layers` and `--base-type`. Its README contains shorthand examples such as `--i-compact` which this parser does not implement. Prefer the verified form:

```bash
LLAMA_QUANTIZE="$LLAMA_DIR/build/bin/llama-quantize" \
  bash "$APEX_DIR/scripts/quantize.sh" \
  --profile i-compact --layers 40 --imatrix "$IMATRIX_FILE" \
  "$SOURCE_GGUF" "$BUILD_DIR/model-i-compact.gguf"
```

Use a matrix corresponding to this model/revision and compatible with the quantizer. The wrapper only warns when an I-profile lacks a matrix and can continue without one. If calibration is required by the selected recipe, verify the matrix exists and was passed; do not label an uncalibrated run as an I-profile result.

For explicit custom rules and a quantization-buffer limit, call the native quantizer directly:

```bash
"$LLAMA_DIR/build/bin/llama-quantize" \
  --tensor-type-file "$BUILD_DIR/tensor-types-custom.txt" \
  --imatrix "$IMATRIX_FILE" --max-buffer-size 1024 \
  "$SOURCE_GGUF" "$BUILD_DIR/model-custom.gguf" Q4_K_M
```

Here `1024` is MiB of the quantization tensor-row buffer, not a whole-process memory cap. `Q4_K_M` is the fallback for tensors not overridden by the reviewed recipe. The wrapper's built-in profiles choose their own fallback; a `--base-type` argument can be superseded by that selection. Direct invocation makes a custom fallback and buffer setting explicit. See [llama-quantize](https://github.com/ggml-org/llama.cpp/blob/41fc7584f0c1d72d9cc1ac46ccae8defc1587f0f/tools/quantize/quantize.cpp).

Start from full/high-precision source weights, preserve them, and write to a new path. Use native `--dry-run` when supported to inspect the planned size before doing the full quantization. It is a size estimate, not a speed or quality prediction.

## Evaluate the result

Read the actual output types, load the artifact in the target engine, then run [quality/capability and resource checks](../validation.md). Compare against a suitable uniform or existing mixed-precision baseline on the same workload. Save the source revision, tensor file, imatrix identity, binary version, command and results.

For a new architecture, sensitivity/allocation tools such as `scripts/generate_sensitivity_configs.py` and `scripts/generate_opt_config.py` are optional starting points from upstream. Their measurements and tensor groups must be redone for the selected architecture; a profile's name is not a universal quality guarantee.
