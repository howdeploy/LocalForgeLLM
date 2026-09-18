#!/usr/bin/env python3
"""Regenerate the English report SVGs. --check is offline and does not render a UI."""
import argparse
import csv
from collections import defaultdict
from html import escape
import math
from pathlib import Path
import textwrap
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
DATA = ROOT / "docs/benchmarks"
INK, MUTED, LINE, BG, SELECTED = "#111111", "#555555", "#cccccc", "#fafafa", "#eaeaea"


def rows(name):
    with (DATA / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def number(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError(f"Non-finite {key}")
    return value


def change(candidate, baseline):
    return 100 * (candidate / baseline - 1)


def bonsai_session():
    completed = [r for r in rows("bonsai-session.csv") if r["status"] == "completed"]
    return completed, sum(number(r, "output_tokens") - 1 for r in completed) * 1000 / sum(
        number(r, "decode_ms") for r in completed
    )


def gemma_phases():
    grouped = defaultdict(list)
    for row in rows("gemma4-cuda-mtp-ram.csv"):
        grouped[row["stage"]].append(row)
    return {
        stage: {
            "mean": sum(number(r, "timed_decode_tokens") for r in group)
            / (sum(number(r, "decode_ms") for r in group) / 1000),
            "low": min(number(r, "decode_tps") for r in group),
            "high": max(number(r, "decode_tps") for r in group),
            "n": len(group),
        }
        for stage, group in grouped.items()
    }


class Page:
    def __init__(self, title, subtitle, hardware, height, date="18 SEP 2026"):
        self.height = height
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" '
            f'viewBox="0 0 1600 {height}" role="img" aria-labelledby="title description">',
            f'<title id="title">{escape(title)}</title>',
            f'<desc id="description">{escape(subtitle + ". " + hardware)}</desc>',
            f'<rect width="1600" height="{height}" fill="{BG}"/>',
            f'<g font-family="DejaVu Sans Mono, monospace" fill="{INK}">',
        ]
        self.text(64, 52, "LOCALFORGELLM / BENCHMARK REPORT", 19, color=MUTED)
        self.text(1536, 52, date, 19, anchor="end", color=MUTED)
        self.text(64, 116, title, 46, bold=True)
        self.text(64, 163, subtitle, 21, color=MUTED)
        self.text(64, 197, hardware, 21, color=MUTED)
        self.line(64, 224, 1536)

    def text(self, x, y, value, size=22, *, bold=False, color=INK, anchor="start"):
        # Monospaced advance is about .602 em; .62 leaves a small font margin.
        width = len(value) * size * .62
        left = x - width if anchor == "end" else x
        if left < 24 or left + width > 1576 or not size <= y <= self.height - 20:
            raise ValueError(f"Text exceeds canvas: {value!r}")
        weight = ' font-weight="700"' if bold else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" '
                          f'fill="{color}" text-anchor="{anchor}"{weight}>{escape(value)}</text>')

    def line(self, x, y, end, color=LINE):
        self.parts.append(f'<path d="M{x} {y}H{end}" stroke="{color}" fill="none"/>')

    def rect(self, x, y, width, height, fill=SELECTED):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{width:.2f}" height="{height}" fill="{fill}"/>')

    def paragraph(self, y, value, width=119, size=20):
        for line in textwrap.wrap(value, width=width):
            self.text(64, y, line, size, color=MUTED)
            y += size + 12
        return y

    def section(self, y, title, detail=""):
        self.text(64, y, title.upper(), 22, bold=True)
        self.line(64, y + 18, 1536)
        if detail:
            self.text(64, y + 49, detail, 19, color=MUTED)

    def metrics(self, items, y=258):
        width = 1472 / len(items)
        for i, (label, value, *notes) in enumerate(items):
            x = 64 + i * width
            self.line(x, y, x + width - 24, INK)
            self.text(x, y + 33, label, 19, color=MUTED)
            self.text(x, y + 96, value, 48, bold=True)
            for j, note in enumerate(notes):
                if len(note) * 19 * .62 > width - 24:
                    raise ValueError(f"Metric note too wide: {note}")
                self.text(x, y + 133 + 29 * j, note, 19, color=MUTED)

    def bar(self, y, label, detail, value, maximum, note="", selected=False, span=None):
        if not 0 <= value <= maximum:
            raise ValueError("Invalid bar domain")
        if selected:
            self.rect(56, y - 9, 1488, 98)
        self.text(72, y + 23, label, 24, bold=True)
        self.text(72, y + 54, detail, 18, color=MUTED)
        if note:
            self.text(72, y + 80, note, 18, color=MUTED)
        self.text(975, y + 38, f"{value:.2f}", 36, bold=True, anchor="end")
        self.text(975, y + 65, "tok/s", 17, anchor="end", color=MUTED)
        start, width = 1040, 448
        self.line(start, y + 32, start + width)
        self.rect(start, y + 24, width * value / maximum, 16, INK if selected else "#999999")
        if span:
            low, high = (start + width * n / maximum for n in span)
            self.line(low, y + 58, high, INK)
            self.parts.append(f'<path d="M{low} {y+53}v10 M{high} {y+53}v10" stroke="{INK}"/>')
        self.line(64, y + 92, 1536)

    def finish(self, source):
        self.line(64, self.height - 78, 1536)
        self.text(64, self.height - 38, source, 18, color=MUTED)
        return "\n".join(self.parts + ["</g>", "</svg>", ""])


def make_bonsai(b):
    speed = lambda key: number(b[key], "decode_tps")
    peak, opus = speed("subscriber_bonsai_q8"), speed("subscriber_opus")
    local, cpu = speed("local_gpu"), speed("local_cpu")
    p = Page("Bonsai 2 / CUDA and GPU cache", "Two machines, two packings. Decode throughput and the settings behind it.",
             "Community: RTX 5070 12 GB / i7-10700K     Local: RTX 4060 8 GB / Ryzen 5 5600", 2310)
    p.metrics([
        ("COMMUNITY / 10K OUTPUT", f"{peak:.2f}", "tok/s / RTX 5070", "PQ2_0 + GPU Q8 KV"),
        ("VS OPUS / SAME REPORT", f"{peak / opus:.2f}x", "10K output comparison", "Different model + runtime"),
        ("LOCAL / SHORT RESPONSE", f"{local:.2f}", "tok/s / RTX 4060", "PTQ1_0 + GPU Q4 KV"),
        ("LOCAL / PROFILE CHANGE", f"{local / cpu:.2f}x", "GPU vs CPU cache", "Microbatch also changed"),
    ])
    p.section(487, "01 / Community report — ap3x0s", "32 GB DDR4 / 32K context / 1 slot / xhigh / 10,000 output tokens per row")
    configs = [
        ("subscriber_apex", "Qwen3.8-27B / APEX nano IQ2", "Stock b10908 / CPU KV + Flash + MTP2"),
        ("subscriber_opus", "Qwen3.8-27B / Opus-Distill-v2", "IQ3_XXS / Stock b10908 / CPU KV + Flash + MTP2"),
        ("subscriber_bonsai_f16", "Ternary Bonsai 2 27B / PQ2_0", "PrismML b10685 / GPU F16 KV + Flash / no MTP"),
        ("subscriber_bonsai_q8", "Ternary Bonsai 2 27B / PQ2_0", "PrismML b10685 / GPU Q8 KV + Flash / no MTP"),
    ]
    for i, (key, label, detail) in enumerate(configs):
        row = b[key]
        note = (f"File {number(row, 'model_disk_gb'):.2f} GB / VRAM {number(row, 'reported_vram_gb'):.2f} GB"
                f" / RAM delta {number(row, 'reported_ram_delta_gb'):.2f} GB")
        p.bar(555 + i * 108, label, detail, speed(key), 60, note, key == "subscriber_bonsai_q8")
    saved_vram = number(b['subscriber_bonsai_f16'], 'reported_vram_gb') - number(b['subscriber_bonsai_q8'], 'reported_vram_gb')
    p.paragraph(1034, f"Q8 vs F16 KV: {change(peak, speed('subscriber_bonsai_f16')):+.1f}% decode, {saved_vram:.2f} reported GB less VRAM.")
    p.paragraph(1070, f"Also reported: {speed('subscriber_bonsai_before'):.2f} tok/s before freeing VRAM; Opus natural EOS: {speed('subscriber_opus_eos'):.2f} tok/s / 6,689 tokens.")
    p.paragraph(1106, "Bonsai hit 10K inside thinking before writing code. Throughput does not establish task success.")
    p.section(1186, "02 / LocalForgeLLM — RTX 4060", "32 GB RAM / 32K context / PrismML b10683 / PTQ1_0 / same 44-token prompt / thinking off")
    p.bar(1252, "CPU Q4 KV + recurrent state", "6 threads / batch 512 / microbatch 64 / 253 output tokens", cpu, 30)
    p.bar(1360, "GPU Q4 KV + recurrent state", "6 threads / batch 512 / microbatch 32 / 248 output tokens", local, 30, selected=True)
    p.metrics([
        ("LONG INPUT / 31,018 TOKENS", f"{speed('local_long'):.2f}", "tok/s / 56 output tokens", "169.68 s full request"),
        ("PROCESS VRAM / SNAPSHOT", "6.24 GiB", "Q4 KV 576 MiB", "Recurrent state 149.62 MiB"),
        ("PACKING / LANGUAGE FILE", "5.95 GB", "PTQ1_0 / local 4060", "PQ2_0 / 5070: 7.21 GB"),
    ], y=1520)
    completed, session_tps = bonsai_session()
    output = sum(int(r["output_tokens"]) for r in completed)
    p.section(1760, "03 / Later llama UI session — RTX 4060", "Same 32K GPU-cache profile / MCP enabled / observational conversation")
    p.bar(1835, "Nine completed generations", "10,786 to 17,989 input tokens, including cached prefixes", session_tps, 30,
          f"{output:,} output tokens / one cancelled stream excluded / reasoning-token split unavailable", selected=True)
    p.paragraph(1975, "Separate smoke checks: reasoning 26.79 tok/s; two MCP skill calls completed in a 76.93 s loop.")
    p.section(2060, "What the result supports")
    p.paragraph(2110, "Ternary kernels reduce weight traffic; GPU cache residency avoids the host path in these profiles.")
    p.paragraph(2144, "Cross-model gains mix several changes. Local headroom reached 98 MiB; no universal 8 GB fit promise.")
    p.paragraph(2178, "Source: subscriber HTML plus local API timings. No controlled quality ranking or instant-peak claim.")
    return p.finish("DATA / docs/benchmarks/bonsai.csv     METHODS + CREDIT / docs/benchmarks/bonsai.md")


def make_reap(r):
    speed = lambda key: number(r[key], "decode_tps")
    gain = change(speed("cache_bypass"), speed("fork_four"))
    wall = change(number(r["cache_bypass"], "mean_wall_seconds"), number(r["fork_four"], "mean_wall_seconds"))
    p = Page("Gemma 4 / prune, rebuild, place", "REAP124 + APEX I-Balanced. Storage and execution are separate experiments.",
             "Rented RTX 4500 Ada 24 GB / Threadripper PRO 5995WX / September 12, 2026", 1620)
    p.metrics([
        ("GGUF / STORAGE CHANGE", f"{change(18959266496, 19508269920):.2f}%", "19.51 to 18.96 GB", "124 of 128 experts/layer"),
        ("PRUNING / DECODE CHANGE", f"{change(speed('apex124'), speed('apex128')):.2f}%", "ABBA / no MTP", "No demonstrated speedup"),
        ("EXPERT CACHE / DECODE", f"{gain:+.2f}%", "Same fork comparison", "MTP2 / 8 runs per config"),
        ("EXPERT CACHE / LATENCY", f"{wall:.2f}%", "Full request time", "RSS increased 2.43 GiB"),
    ])
    p.section(487, "01 / Build lineage")
    p.text(64, 553, "Heretic BF16  →  REAP124  →  BF16 GGUF  →  fresh imatrix  →  APEX", 28, bold=True)
    p.paragraph(602, "30 layers / top-k stays 8 / 44,032 imatrix tokens / exact tensor recipe / native llama-quantize")
    p.paragraph(638, "Pruning control: 37.46 → 37.26 tok/s. Experimental quality gate; no proved <=5% loss bound.")
    p.section(723, "02 / Same REAP124 weights — change expert placement", "512 input / 256 output / 32K / 6 threads / Flash / Q8 KV / MTP2 / no prompt cache")
    configs = [
        ("stock_four", "Stock b10883 / 4 GPU MoE blocks", "Reference runtime"),
        ("fork_four", "Same fork / 4 GPU MoE blocks", "Control for the cache comparison"),
        ("cache_normal", "2,200 MiB cache / normal prefill", "Better decode, slower full request"),
        ("cache_pp_cpu", "2,200 MiB cache / CPU prefill", "Dense prefill disabled"),
        ("cache_bypass", "2,200 MiB cache / prefill bypass", "475 hot experts / cold experts stay in RAM"),
    ]
    for i, (key, label, detail) in enumerate(configs):
        row = r[key]
        note = f"Prefill {number(row, 'prefill_tps'):.2f} tok/s / full request {number(row, 'mean_wall_seconds'):.3f} s"
        p.bar(792 + i * 108, label, detail, speed(key), 40, note, key == "cache_bypass")
    p.section(1414, "Why the best configuration helps")
    p.paragraph(1464, "Hot copies speed decode; prefill bypass limits the prompt penalty. Extra host RAM is the tradeoff.")
    p.paragraph(1498, "Corrected strided profiler. Sequential hot/cold fallback observed. These are not RTX 4060 rates.")
    return p.finish("DATA / docs/benchmarks/reap.csv     TOOLS + RECIPE + LIMITS / docs/implementations/reap.md")


def make_cuda(g):
    p = Page("Gemma 4 / CUDA, MTP and RAM", "Heretic APEX I-Balanced: 19.51 GB target + 0.46 GB Q8 MTP head. Weights unchanged.",
             "RTX 4060 8 GB / Ryzen 5 5600 / 32 GB RAM / llama.cpp b10883 / September 11, 2026", 1680)
    p.metrics([
        ("BEST PHASE / 4 RESPONSES", f"{g['06']['mean']:.2f}", "tok/s / CUDA + MTP2", "20 GiB service cap"),
        ("BEST COMPLETED RESPONSE", f"{g['06']['high']:.2f}", "tok/s / 1,019 output", "52.53 s decode interval"),
        ("MTP / LATER CUDA PHASES", f"{change(g['06']['mean'], g['07']['mean']):+.1f}%", "Different chat requests", "Observed, not isolated"),
        ("INITIAL CUDA COMPILE", "10m 30s", "4 workers / 499 steps", "2.1 GiB peak build RAM"),
    ])
    p.section(487, "The tuning sequence / 19 completed responses", "Weighted means; thin lines show observed min–max across replies, not confidence intervals.")
    labels = [
        ("01", "Vulkan / no MTP / 11 GiB", "Initial reference / mmap"),
        ("02", "Vulkan / MTP2 / 11 GiB", "Separate compatible Q8 assistant"),
        ("03", "CUDA / MTP2 / 11 GiB", "First backend switch"),
        ("04", "CUDA / MTP2 / 20 GiB", "Service cap raised in the same process"),
        ("05", "CUDA / MTP2 / direct load", "Reverted: less than 1 GiB available system RAM"),
        ("06", "CUDA / MTP2 / 20 GiB", "mmap restored / best phase mean"),
        ("07", "CUDA / no MTP / 20 GiB", "Later MTP-off comparison"),
        ("08", "CUDA / MTP2 / 11 GiB", "Later low-cap comparison"),
    ]
    for i, (key, label, detail) in enumerate(labels):
        d = g[key]
        p.bar(555 + i * 105, f"{key} / {label}", f"{detail} / n={d['n']}", d["mean"], 20,
              selected=key == "06", span=(d["low"], d["high"]))
    p.section(1450, "What helped — and what the data cannot isolate")
    p.paragraph(1500, "GPU: attention + 3 expert blocks + Q8 KV. CPU: experts in 27/30 blocks. 32K / 1 slot / 6 threads.")
    p.paragraph(1534, "RAM headroom, MTP and cache state matter. CUDA alone first measured 14.83 → 14.01 tok/s (-5.5%).")
    p.paragraph(1568, "Different prompts and live histories. Phase percentages are not additive; no full-32K quality test.")
    return p.finish("DATA + METHODS / docs/benchmarks/gemma4-cuda-mtp-ram.md and .csv")


def make_mtp(g):
    p = Page("Gemma 4 / MTP in context", "A compatible assistant proposes tokens; the target verifies them. Measure the complete request.",
             "Local: RTX 4060 8 GB / Ryzen 5 5600 / Heretic APEX I-Balanced / Q8 MTP assistant", 1260)
    p.metrics([
        ("EARLY VULKAN / MTP2", f"{g['02']['mean']:.2f}", "tok/s / 2 responses", "+51.1% observed gap"),
        ("LATER CUDA / MTP2", f"{g['06']['mean']:.2f}", "tok/s / 4 responses", "20 GiB service cap"),
        ("LATER CUDA / MTP OFF", f"{g['07']['mean']:.2f}", "tok/s / 4 responses", "Same cap / other prompts"),
    ])
    p.section(487, "Original Vulkan timing / September 11", "Same main placement; different requests. The observed gap is not a causal MTP gain.")
    for i, row in enumerate(rows("gemma4-cuda-mtp-ram.csv")[:3]):
        mode = "MTP off" if row["stage"] == "01" else "MTP depth 2"
        p.bar(555 + i * 108, mode, f"{row['decode_tokens']} output tokens / {number(row, 'decode_ms') / 1000:.2f} s decode",
              number(row, "decode_tps"), 20, selected=i == 2)
    p.section(940, "Community paired controls / different model and machine")
    p.paragraph(990, "RTX 2070 Max-Q 8 GB / i7-8750H / QAT 4-bit + QAT head / CUDA / repeated coding workload.")
    p.text(64, 1038, "Temperature 1: 23.1 → 24.0 tok/s (+3.9%; within reported noise)", 24, bold=True)
    p.text(64, 1080, "Greedy:        22.9 → 27.1 tok/s (+18.3%; paired trials)", 24, bold=True)
    p.paragraph(1124, "Our Q8 label belongs to the 0.46 GB head, not the 19.51 GB target. Vision with MTP was not tested.")
    return p.finish("TIMINGS + COMMUNITY SOURCES / docs/benchmarks/gemma4-mtp.md     LATER PHASES / gemma4-cuda-mtp-ram.csv")


def make_comparison():
    p = Page("Qwen3.6 / three deployment reports", "35B-A3B. Hardware, quantization and workloads differ; memory columns have different meanings.",
             "Local measurement: September 10, 2026 / 32K configured / 28 requests", 1000)
    p.section(282, "Decode / independent reports", "Bars share a zero origin. These are deployment observations, not a controlled framework ranking.")
    data = [
        ("LocalForgeLLM / APEX I-Compact", "RTX 4060 8 GB / Ryzen 5 5600 / Vulkan", 21.11, "13.43 GiB peak process RSS / 4.07 GiB model VRAM", True),
        ("Colibri / int4 / warm", "RTX 3070 8 GB / Threadripper 3945WX / CUDA", 9.9, "40 GB reported peak RSS / 200-token decode", False),
        ("FreeToken / NVFP4", "RTX 4060 Laptop 8 GB / i9-13900H / coding workload", 39.3, "32 GiB installed RAM; process RSS not supplied", False),
    ]
    for i, (label, detail, value, note, selected) in enumerate(data):
        p.bar(355 + i * 120, label, detail, value, 40, note, selected)
    p.section(786, "Read the comparison with its resource budget")
    p.paragraph(836, "Local rate: 2.13x Colibri warm; 46.3% below FreeToken. All three configurations remain visible.")
    p.paragraph(870, "CPU/GPU placement enables the local fit. Different artifacts and workloads prevent a causal claim.")
    return p.finish("LOCAL SETTINGS + PRIMARY COMPARISON SOURCES / docs/README.md#comparison-with-colibri-and-freetoken")


def make_gemma_comparison(g):
    p = Page("Gemma 4 / deployment references", "26B-A4B family. Distinct weights, hardware and evidence; higher decode is not a quality score.",
             "Local CUDA update: 18.80 weighted tok/s / best completed-response average: 19.38 tok/s", 1200)
    p.section(282, "Decode / configurations named", "Same zero-based bar scale. External values are author reports, not reruns by LocalForgeLLM.")
    data = [
        ("LocalForgeLLM / CUDA + MTP2", "RTX 4060 8 GB / Ryzen 5 5600 / 32 GB RAM", g["06"]["mean"], "Heretic APEX 19.51 GB + Q8 head 0.46 GB / 4 replies", True),
        ("llama.cpp / community CUDA", "RTX 2070 Max-Q 8 GB / i7-8750H / 31 GB RAM", 24., "QAT 4-bit + QAT MTP / 32K / temp 1 / trimmed mean", False),
        ("llama.cpp / community Vulkan", "Same RTX 2070 Max-Q rig / earlier backend report", 4.9, "QAT 4-bit / approximately 4.9 / different workload", False),
        ("Ollama / full Q8 reference", "NVIDIA GB10 / 128 GB unified memory / Ollama 0.20.3", 45.2, "About 28 GB reported target / 7 informal workloads", False),
        ("FreeToken / patched user report", "RTX 4080 SUPER 16 GB / FreeToken 0.1.2", 179., "QAT UD-Q4_K_XL / issue #188 / no paired control", False),
    ]
    for i, (label, detail, value, note, selected) in enumerate(data):
        p.bar(354 + i * 120, label, detail, value, 180, note, selected)
    p.section(1020, "The tradeoff is explicit")
    p.paragraph(1070, "Our mixed-precision Heretic target is larger than the QAT 4-bit reference. No claim of universal lead.")
    p.paragraph(1104, "Colibri had no Gemma entry in the inspected roster. Vendor peak claims are not substituted for tests.")
    return p.finish("PRIMARY SOURCES / docs/benchmarks/gemma4-mtp.md     LOCAL UPDATE / gemma4-cuda-mtp-ram.md")


def make_workflow():
    p = Page("One workflow / different bottlenecks", "Give the agent a task, a model and a real resource budget. Save the working profile and its evidence.",
             "Dense + MoE / published weights + derived artifacts / local inference + optional hosted decisions", 1130)
    p.section(285, "Choose the work")
    stages = [
        ("01 / INSTALL", "Model + packing + compatible kernels", "Bonsai PTQ1_0 or PQ2_0 needs the matching ternary runtime."),
        ("02 / TUNE", "Placement + context + KV + batching + MTP", "4060: GPU Q4 KV. 5070: GPU Q8 KV. Gemma: CPU experts + MTP."),
        ("03 / BUILD", "Full weights → REAP → calibration → APEX", "Pruning changes topology; quantization changes precision. Check quality after both."),
    ]
    for i, (label, title, detail) in enumerate(stages):
        y = 350 + i * 132
        p.text(64, y, label, 22, bold=True)
        p.text(350, y, title, 25, bold=True)
        p.text(350, y + 41, detail, 19, color=MUTED)
        p.line(64, y + 76, 1536)
    p.section(786, "Run → measure → check → save → repeat")
    p.paragraph(839, "Record hardware, versions, prompt/decode time, RAM/VRAM definitions and failures. Keep a rollback.")
    p.text(64, 910, "OPTIONAL / JEV + BROWSER-USE + MCP", 22, bold=True)
    p.paragraph(951, "Jev chooses typed actions; the local LLM writes text; the harness owns tools and permissions.")
    p.paragraph(985, "Reuse selected Hermes MCP tools and skill text in llama UI. Verify outcomes, not just valid JSON.")
    return p.finish("GUIDES / SKILL.md + docs/README.md     OPTIONAL API / docs/interfaces/jev.md")


def documents():
    b = {r["id"]: r for r in rows("bonsai.csv")}
    r = {r["id"]: r for r in rows("reap.csv")}
    g = gemma_phases()
    return {
        "bonsai.svg": make_bonsai(b), "reap.svg": make_reap(r),
        "gemma4-cuda-mtp-ram.svg": make_cuda(g), "gemma4-mtp.svg": make_mtp(g),
        "comparison.svg": make_comparison(), "gemma4-comparison.svg": make_gemma_comparison(g),
        "how-it-works.svg": make_workflow(),
    }


def check_data():
    """Check source invariants, timing arithmetic and the main published ratios."""
    b = {r["id"]: r for r in rows("bonsai.csv")}
    assert len(b) == 9
    for key in ("local_cpu", "local_gpu", "local_long"):
        row = b[key]
        measured = (number(row, "output_tokens") - 1) * 1000 / number(row, "decode_ms")
        assert math.isclose(measured, number(row, "decode_tps"), rel_tol=1e-10)
        assert number(row, "wall_seconds") >= (number(row, "prompt_ms") + number(row, "decode_ms")) / 1000
    ratio = number(b["subscriber_bonsai_q8"], "decode_tps") / number(b["subscriber_opus"], "decode_tps")
    assert round(ratio, 2) == 5.60 and round(100 * (ratio - 1), 1) == 460.1
    session, session_tps = bonsai_session()
    assert len(session) == 9 and len(rows("bonsai-session.csv")) == 10
    assert sum(int(r["output_tokens"]) for r in session) == 7355
    assert round(session_tps, 2) == 19.58
    for row in session:
        measured = (number(row, "output_tokens") - 1) * 1000 / number(row, "decode_ms")
        assert abs(measured - number(row, "decode_tps")) <= 0.005
        assert number(row, "prompt_evaluated_tokens") <= number(row, "input_tokens")
        assert int(row["slot_tokens_end"]) == int(row["input_tokens"]) + int(row["output_tokens"]) - 1
    g = gemma_phases()
    assert sum(d["n"] for d in g.values()) == 19
    assert round(g["06"]["mean"], 2) == 18.80
    assert round(g["06"]["high"], 2) == 19.38
    r = {row["id"]: row for row in rows("reap.csv")}
    assert len(r) == 7
    assert round(change(number(r["cache_bypass"], "decode_tps"), number(r["fork_four"], "decode_tps")), 2) == 8.07
    assert round(change(number(r["apex124"], "decode_tps"), number(r["apex128"], "decode_tps")), 2) == -0.52


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check data and tracked SVG freshness without writing")
    args = parser.parse_args()
    check_data()
    for name, content in documents().items():
        ET.fromstring(content)
        path = ASSETS / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"Stale asset: {path}; run scripts/render_benchmarks.py")
        else:
            path.write_text(content)
    print("PASS: benchmark arithmetic, SVG XML, text canvas bounds and 7 current assets")
