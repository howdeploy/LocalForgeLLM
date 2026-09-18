# Benchmark artwork

All seven figures use English copy and the existing LocalForgeLLM report design: `#fafafa` background, `#111111` ink, gray rules, monochrome bars, rectangular row emphasis and monospaced typography. The reference is this repository's original comparison SVGs and its September 11 CUDA/MTP/RAM report. The subscriber HTML supplies data and attribution; it does not replace the project's visual language.

The common canvas is 1600 pixels wide. Hierarchy is report title → hardware and evidence scope → headline measurements → zero-based comparisons → interpretation and source footer. No stock photos, generated images or new brand palette are needed. A reported speed is an interval average; the best row is highlighted without dropping slower trials or external results that exceed ours.

| Asset | Evidence and purpose |
|:--|:--|
| [Bonsai](bonsai.svg) | [Community and local CSV](../benchmarks/bonsai.csv), [later session CSV](../benchmarks/bonsai-session.csv); distinct 5070, 4060 tuning and interactive-session panels |
| [REAP and caching](reap.svg) | [Rented-server CSV](../benchmarks/reap.csv); storage, pruning and placement separated |
| [CUDA / MTP / RAM](gemma4-cuda-mtp-ram.svg) | [19-response CSV](../benchmarks/gemma4-cuda-mtp-ram.csv); weighted means and observed ranges |
| [MTP](gemma4-mtp.svg) | Same local CSV plus [pinned community controls](../benchmarks/gemma4-mtp.md) |
| [Gemma comparisons](gemma4-comparison.svg) | Updated local CUDA phase plus [attributed external results](../benchmarks/gemma4-mtp.md) |
| [Qwen comparisons](comparison.svg) | Historical [local and external reports](../README.md#comparison-with-colibri-and-freetoken) |
| [Workflow](how-it-works.svg) | Install, tune, build and optional Jev integration |

Regenerate from the repository root with Python's standard library:

```bash
python3 scripts/render_benchmarks.py
python3 scripts/render_benchmarks.py --check
```

The check recalculates native decode rates and headline ratios, validates SVG XML and conservative monospaced text bounds, and detects stale tracked SVGs. External historical comparison values are transcribed from the linked reports in the generator; locally aggregated phase values and new Bonsai/REAP figures come from CSV. Review source identity and scope when changing either.

The existing README also embeds a PNG export. With librsvg's `rsvg-convert` installed, refresh it after changing the SVG:

```bash
rsvg-convert docs/assets/gemma4-cuda-mtp-ram.svg \
  -o docs/assets/gemma4-cuda-mtp-ram.png
```

The same command exports any other SVG for sharing. SVGs retain accessible titles and descriptions and are the editable source of the graphics. Numeric/XML checks and PNG generation are not a visual review; this update does not claim browser or screenshot QA.
