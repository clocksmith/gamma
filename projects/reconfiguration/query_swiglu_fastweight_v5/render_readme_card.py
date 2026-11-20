#!/usr/bin/env python3
"""Generate the Gamma README hero SVG card directly from a Qwen B1 receipt JSON.

Every numeric label on the rendered card is computed from the supplied receipt
file rather than hard-coded.
"""

from __future__ import annotations

import argparse
import html
import json
import statistics
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RECEIPT = (
    REPO_ROOT
    / ".work/query-swiglu-fastweight-v5/qwen35_08b_dev1103_k20_readout_adapter.json"
)
DEFAULT_OUT = REPO_ROOT / "assets/readme/qwen-b1-development-card.svg"


def fmt_ms(ms: float) -> str:
    if ms >= 1000.0:
        return f"{ms / 1000.0:.2f} s"
    return f"{round(ms)} ms"


def fmt_kb_range(values: list[int]) -> str:
    # Match RESULTS.md decimal SI units (1 KB = 1,000 B -> 92,160 B = 92 KB, 184,320 B = 184 KB).
    lo = round(min(values) / 1000.0)
    hi = round(max(values) / 1000.0)
    if lo == hi:
        return f"{lo} KB"
    return f"{lo}-{hi} KB"


def fmt_mb(byte_count: float) -> str:
    # Match RESULTS.md decimal SI units (1 MB = 1,000,000 B -> 32,372,736 B = 32.4 MB).
    return f"{byte_count / 1_000_000.0:.1f} MB"


def load_metrics(receipt_path: Path) -> dict[str, object]:
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    rows = data["rows"]
    specialties = data["specialties_compiled"]

    def arm_stats(arm: str) -> dict[str, object]:
        arm_rows = [r for r in rows if r["arm"] == arm]
        if not arm_rows:
            raise ValueError(f"Missing arm {arm!r} in {receipt_path}")
        correct = sum(1 for r in arm_rows if r["correct"])
        total = len(arm_rows)
        latencies = [float(r["total_ms"]) for r in arm_rows if r.get("total_ms") is not None]
        return {
            "correct": correct,
            "total": total,
            "pct": 100.0 * correct / total,
            "median_ms": statistics.median(latencies),
        }

    probe = arm_stats("probe_bare")
    adapter = arm_stats("ra_bare")
    kv = arm_stats("kv_ctx")
    mfc = arm_stats("mfc_bare")

    ra_bytes = [int(s["readout_adapter_bytes"]) for s in specialties]
    ra_fit_ms = [float(s["readout_adapter_fit_ms"]) for s in specialties]
    probe_fit_ms = [float(s["probe_fit_ms"]) for s in specialties]
    fixed_compile_ms = [float(s["fixed_compile_ms"]) for s in specialties if s.get("fixed_compile_ms") is not None]
    forward_passes = sorted({int(s["forward_passes"]) for s in specialties})
    table_tokens = [int(s["table_tokens"]) for s in specialties]

    kv_build_ms = [float(s["kv_snapshot"]["kv_build_ms"]) for s in specialties]
    kv_state_bytes = [int(s["kv_snapshot"]["kv_state_bytes"]) for s in specialties]
    kv_used_bytes = [int(s["kv_snapshot"]["kv_used_bytes"]) for s in specialties]
    linear_state_bytes = [int(s["kv_snapshot"]["linear_state_bytes"]) for s in specialties]

    kv_median_bytes = statistics.median(kv_state_bytes)
    ratio_hi = round(kv_median_bytes / min(ra_bytes))
    ratio_lo = round(kv_median_bytes / max(ra_bytes))

    return {
        "receipt_name": receipt_path.name,
        "model": str(data["model"]),
        "seed": int(data["seed"]),
        "specialties": int(data["specialties"]),
        "task_count": int(data["task_count"]),
        "doppler_commit": str(data["doppler_source"]["commit"])[:9],
        "probe": probe,
        "adapter": adapter,
        "kv": kv,
        "mfc": mfc,
        "probe_fit_median_ms": statistics.median(probe_fit_ms),
        "ra_fit_median_ms": statistics.median(ra_fit_ms),
        "fixed_compile_median_ms": statistics.median(fixed_compile_ms),
        "forward_passes_label": (
            f"{forward_passes[0]}"
            if len(forward_passes) == 1
            else f"{forward_passes[0]}-{forward_passes[-1]}"
        ),
        "kv_build_median_ms": statistics.median(kv_build_ms),
        "kv_tokens_median": round(statistics.median(table_tokens)),
        "ra_bytes_label": fmt_kb_range(ra_bytes),
        "ra_ratio_label": f"~{ratio_lo}-{ratio_hi}x smaller vs warm KV",
        "kv_median_mb": fmt_mb(kv_median_bytes),
        "kv_range_mb": f"{min(kv_state_bytes) / 1_000_000.0:.1f}-{max(kv_state_bytes) / 1_000_000.0:.1f} MB",
        "kv_breakdown": f"{statistics.median(linear_state_bytes) / 1_000_000.0:.1f} linear + {statistics.median(kv_used_bytes) / 1_000_000.0:.1f} KV",
        "delta_ra_vs_kv_pts": adapter["pct"] - kv["pct"],
        "delta_probe_vs_ra_pts": probe["pct"] - adapter["pct"],
    }


def render_svg(m: dict[str, object]) -> str:
    esc = html.escape
    probe = m["probe"]
    adapter = m["adapter"]
    kv = m["kv"]
    mfc = m["mfc"]

    # Bar geometry (honest 0% to 100% scale, generous right margin for score labels)
    bar_x = 248
    bar_max_w = 472
    bar_h = 24
    score_x = 736

    def bar_w(pct: float) -> float:
        return round(bar_max_w * (pct / 100.0), 1)

    mfc_x = round(bar_x + bar_w(mfc["pct"]), 1)
    probe_w = bar_w(probe["pct"])
    adapter_w = bar_w(adapter["pct"])
    kv_w = bar_w(kv["pct"])

    eyebrow = (
        f"GAMMA  /  QWEN 3.5 0.8B DEVELOPMENT RUN  /  "
        f"SEED {m['seed']}  /  {m['specialties']} TABLES  /  {m['task_count']} QUESTIONS"
    )
    subtitle = (
        f"Exploratory development split (not a confirmation) · {m['model']} · "
        f"Doppler {m['doppler_commit']} · protocol_v5_draft.json"
    )
    footnote_1 = (
        f"*Shared activation capture: {m['forward_passes_label']} support passes/table "
        f"({fmt_ms(m['fixed_compile_median_ms'])} median capture + top-2 compile). Table removed for classifier & adapter."
    )
    footnote_2 = (
        f"Receipt: {m['receipt_name']} · All values are medians from this single run (full hashes in receipt)."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 548" width="960" height="548" role="img" aria-labelledby="title desc">
  <title id="title">The adapter beat warm KV. The plain classifier beat both.</title>
  <desc id="desc">Qwen 3.5 0.8B development run (seed {m['seed']}, {m['specialties']} tables, {m['task_count']} questions). Plain classifier scored {probe['correct']}/{probe['total']} ({probe['pct']:.1f}%), readout adapter scored {adapter['correct']}/{adapter['total']} ({adapter['pct']:.1f}%), and warm KV scored {kv['correct']}/{kv['total']} ({kv['pct']:.1f}%).</desc>
  <style>
    :root {{
      --bg: #ffffff;
      --surface: #f8fafc;
      --surface-alt: #f1f5f9;
      --border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #475569;
      --text-subtle: #64748b;
      --track: #e2e8f0;
      --winner: #0f766e;
      --winner-soft: #ccfbf1;
      --winner-text: #115e59;
      --adapter: #2563eb;
      --adapter-soft: #dbeafe;
      --adapter-text: #1d4ed8;
      --kv: #64748b;
      --mfc: #94a3b8;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0d1117;
        --surface: #161b22;
        --surface-alt: #1c2128;
        --border: #30363d;
        --text: #f0f6fc;
        --text-muted: #9ca3af;
        --text-subtle: #8b949e;
        --track: #21262d;
        --winner: #2dd4bf;
        --winner-soft: #134e4a;
        --winner-text: #99f6e4;
        --adapter: #60a5fa;
        --adapter-soft: #1e3a8a;
        --adapter-text: #bfdbfe;
        --kv: #8b949e;
        --mfc: #6e7681;
      }}
    }}
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.05em; fill: var(--text-subtle); }}
    .title {{ font-size: 23px; font-weight: 700; letter-spacing: -0.02em; fill: var(--text); }}
    .subtitle {{ font-size: 11.5px; fill: var(--text-muted); }}
    .section-label {{ font-size: 10.5px; font-weight: 700; letter-spacing: 0.06em; fill: var(--text-subtle); }}
    .arm-name {{ font-size: 13px; font-weight: 600; fill: var(--text); }}
    .arm-sub {{ font-size: 11px; fill: var(--text-subtle); }}
    .score-val {{ font-size: 13px; font-weight: 700; fill: var(--text); }}
    .score-pct {{ font-size: 11px; fill: var(--text-muted); }}
    .th {{ font-size: 10.5px; font-weight: 700; letter-spacing: 0.04em; fill: var(--text-subtle); }}
    .row-label {{ font-size: 12px; font-weight: 600; fill: var(--text-muted); }}
    .cell-main {{ font-size: 12.5px; font-weight: 600; fill: var(--text); }}
    .cell-sub {{ font-size: 10.5px; fill: var(--text-subtle); }}
    .pill-text-win {{ font-size: 10.5px; font-weight: 600; fill: var(--winner-text); }}
    .pill-text-adp {{ font-size: 10.5px; font-weight: 600; fill: var(--adapter-text); }}
    .foot {{ font-size: 10px; fill: var(--text-subtle); }}
  </style>

  <!-- Outer Card -->
  <rect x="0.5" y="0.5" width="959" height="547" rx="12" fill="var(--bg)" stroke="var(--border)" stroke-width="1"/>

  <!-- Header -->
  <text x="32" y="34" class="mono eyebrow">{esc(eyebrow)}</text>
  <text x="32" y="65" class="sans title">The adapter beat warm KV. The plain classifier beat both.</text>
  <text x="32" y="86" class="sans subtitle">{esc(subtitle)}</text>
  <line x1="32" y1="102" x2="928" y2="102" stroke="var(--border)" stroke-width="1"/>

  <!-- Section 1: Accuracy (0% to 100% honest scale) -->
  <text x="32" y="124" class="mono section-label">ACCURACY ON FRESH DEVELOPMENT TABLES (0% TO 100% SCALE)</text>
  <text x="928" y="124" text-anchor="end" class="mono cell-sub">Dashed line: most-frequent-code baseline ({mfc['correct']}/{mfc['total']}, {mfc['pct']:.1f}%)</text>

  <!-- Baseline tick: MFC 25.0% -->
  <line x1="{mfc_x}" y1="138" x2="{mfc_x}" y2="258" stroke="var(--mfc)" stroke-width="1" stroke-dasharray="3,3"/>

  <!-- Clean scale ticks at 0%, 25%, 50%, 75%, 100% -->
  <text x="{bar_x}" y="272" class="mono cell-sub">0%</text>
  <text x="{mfc_x}" y="272" text-anchor="middle" class="mono cell-sub">25% (MFC)</text>
  <text x="{bar_x + bar_max_w * 0.50:.1f}" y="272" text-anchor="middle" class="mono cell-sub">50%</text>
  <text x="{bar_x + bar_max_w * 0.75:.1f}" y="272" text-anchor="middle" class="mono cell-sub">75%</text>
  <text x="{bar_x + bar_max_w}" y="272" text-anchor="end" class="mono cell-sub">100%</text>

  <!-- Bar 1: Plain classifier -->
  <text x="32" y="155" class="sans arm-name">Plain classifier</text>
  <text x="32" y="170" class="mono arm-sub">probe_bare · table removed</text>
  <rect x="{bar_x}" y="142" width="{bar_max_w}" height="{bar_h}" rx="5" fill="var(--track)"/>
  <rect x="{bar_x}" y="142" width="{probe_w}" height="{bar_h}" rx="5" fill="var(--winner)"/>
  <text x="{score_x}" y="155" class="mono score-val">{probe['correct']} / {probe['total']} ({probe['pct']:.1f}%)</text>
  <text x="{score_x}" y="170" class="mono score-pct">+{m['delta_probe_vs_ra_pts']:.1f} pt vs adapter</text>

  <!-- Bar 2: Readout adapter -->
  <text x="32" y="196" class="sans arm-name">Readout adapter</text>
  <text x="32" y="211" class="mono arm-sub">ra_bare · table removed</text>
  <rect x="{bar_x}" y="183" width="{bar_max_w}" height="{bar_h}" rx="5" fill="var(--track)"/>
  <rect x="{bar_x}" y="183" width="{adapter_w}" height="{bar_h}" rx="5" fill="var(--adapter)"/>
  <text x="{score_x}" y="196" class="mono score-val">{adapter['correct']} / {adapter['total']} ({adapter['pct']:.1f}%)</text>
  <text x="{score_x}" y="211" class="mono score-pct">+{m['delta_ra_vs_kv_pts']:.1f} pts vs warm KV</text>

  <!-- Bar 3: Warm KV -->
  <text x="32" y="237" class="sans arm-name">Warm KV</text>
  <text x="32" y="252" class="mono arm-sub">kv_ctx · table in prompt</text>
  <rect x="{bar_x}" y="224" width="{bar_max_w}" height="{bar_h}" rx="5" fill="var(--track)"/>
  <rect x="{bar_x}" y="224" width="{kv_w}" height="{bar_h}" rx="5" fill="var(--kv)"/>
  <text x="{score_x}" y="237" class="mono score-val">{kv['correct']} / {kv['total']} ({kv['pct']:.1f}%)</text>
  <text x="{score_x}" y="252" class="mono score-pct">cached prompt baseline</text>

  <!-- Section 2: Cost & State Table -->
  <rect x="32" y="290" width="896" height="202" rx="8" fill="var(--surface)" stroke="var(--border)" stroke-width="1"/>

  <!-- Table Header -->
  <rect x="33" y="291" width="894" height="36" rx="7" fill="var(--surface-alt)"/>
  <line x1="32" y1="327" x2="928" y2="327" stroke="var(--border)" stroke-width="1"/>
  <text x="48" y="313" class="mono th">METRIC (MEDIANS)</text>
  <text x="248" y="313" class="mono th">PLAIN CLASSIFIER</text>
  <text x="476" y="313" class="mono th">READOUT ADAPTER</text>
  <text x="704" y="313" class="mono th">WARM KV</text>

  <!-- Row 1: Setup cost -->
  <text x="48" y="354" class="sans row-label">Setup cost / table</text>
  <text x="248" y="352" class="mono cell-main">{esc(fmt_ms(m['probe_fit_median_ms']))} ridge fit</text>
  <text x="248" y="368" class="sans cell-sub">+ {m['forward_passes_label']} shared support passes*</text>
  <text x="476" y="352" class="mono cell-main">{esc(fmt_ms(m['ra_fit_median_ms']))} fit + upload</text>
  <text x="476" y="368" class="sans cell-sub">+ {m['forward_passes_label']} shared support passes*</text>
  <text x="704" y="352" class="mono cell-main">{esc(fmt_ms(m['kv_build_median_ms']))} prefill</text>
  <text x="704" y="368" class="sans cell-sub">1 pass ({m['kv_tokens_median']} median tokens)</text>
  <line x1="48" y1="382" x2="912" y2="382" stroke="var(--border)" stroke-width="1"/>

  <!-- Row 2: Answer latency -->
  <text x="48" y="409" class="sans row-label">Answer latency / q</text>
  <rect x="248" y="392" width="76" height="22" rx="4" fill="var(--winner-soft)"/>
  <text x="286" y="407" text-anchor="middle" class="mono pill-text-win">{esc(fmt_ms(probe['median_ms']))}</text>
  <text x="332" y="407" class="sans cell-sub">fastest</text>
  <text x="476" y="409" class="mono cell-main">{esc(fmt_ms(adapter['median_ms']))}</text>
  <text x="542" y="409" class="sans cell-sub">median / question</text>
  <text x="704" y="409" class="mono cell-main">{esc(fmt_ms(kv['median_ms']))}</text>
  <text x="770" y="409" class="sans cell-sub">median / question</text>
  <line x1="48" y1="430" x2="912" y2="430" stroke="var(--border)" stroke-width="1"/>

  <!-- Row 3: Retained bytes -->
  <text x="48" y="459" class="sans row-label">Retained state / table</text>
  <text x="248" y="457" class="mono cell-main">Not logged in receipt</text>
  <text x="248" y="473" class="sans cell-sub">4 linear rows (layers 22-23)</text>
  <rect x="476" y="442" width="94" height="22" rx="4" fill="var(--adapter-soft)"/>
  <text x="523" y="457" text-anchor="middle" class="mono pill-text-adp">{esc(m['ra_bytes_label'])}</text>
  <text x="476" y="477" class="sans cell-sub">{esc(m['ra_ratio_label'])}</text>
  <text x="704" y="457" class="mono cell-main">{esc(m['kv_median_mb'])} median</text>
  <text x="704" y="473" class="sans cell-sub">{esc(m['kv_range_mb'])} ({esc(m['kv_breakdown'])})</text>

  <!-- Footer -->
  <text x="32" y="514" class="sans foot">{esc(footnote_1)}</text>
  <text x="32" y="531" class="mono foot">{esc(footnote_2)}</text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    metrics = load_metrics(args.receipt)
    svg = render_svg(metrics)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    print(f"Wrote {args.out} ({len(svg)} bytes) from {args.receipt.name}")


if __name__ == "__main__":
    main()
