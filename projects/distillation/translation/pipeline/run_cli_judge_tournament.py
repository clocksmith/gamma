#!/usr/bin/env python3
"""Run a GEPA-style tournament over Codex-judged translation dataset recipes."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PIPELINE_DIR = Path(__file__).resolve().parent
FILTER_SCRIPT = PIPELINE_DIR / "filter_translation_pairs_with_cli_judge.py"
SCORE_SCRIPT = PIPELINE_DIR / "score_translation_pair_datasets.py"
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "frozen_best5_refine"
    / "frozen_best5.p10"
    / "pack_04"
    / "frozen_best5.pack_04.replace10.jsonl"
)
DEFAULT_OUT_DIR = (
    PROJECT_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "training_data"
    / "cli_judge_tournament"
)
DEFAULT_CODEX_COMMAND = (
    "codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write "
    f"-C {PROJECT_ROOT} --color never -o {{response_file}} -"
)


@dataclass(frozen=True)
class Recipe:
    name: str
    judge_profile: str
    rewrite_mode: str = "queue"
    min_adequacy: float = 4.0
    min_literalness: float = 3.5
    min_entity_number_preservation: float = 4.0
    min_confidence: float = 0.55
    extra_instruction: str = ""


def _default_recipes() -> list[Recipe]:
    return [
        Recipe(
            name="balanced_ref",
            judge_profile="balanced",
            extra_instruction="Target a balanced external benchmark reference; keep only rows useful for EN<->ES SFT.",
        ),
        Recipe(
            name="strict_literal",
            judge_profile="strict_literal",
            min_adequacy=4.25,
            min_literalness=4.0,
            min_entity_number_preservation=4.25,
            min_confidence=0.60,
            extra_instruction="Favor rows that teach literal coverage over fluent paraphrase.",
        ),
        Recipe(
            name="entity_guard",
            judge_profile="entity_guard",
            min_entity_number_preservation=4.5,
            min_confidence=0.60,
            extra_instruction="Names, dates, numbers, times, and units are decisive.",
        ),
        Recipe(
            name="external_wmt",
            judge_profile="external_wmt",
            min_adequacy=4.25,
            min_literalness=3.75,
            min_confidence=0.60,
            extra_instruction="Prefer rows that would not look out of place in WMT-style external evaluation.",
        ),
        Recipe(
            name="rewrite_surgeon",
            judge_profile="rewrite_surgeon",
            rewrite_mode="queue",
            min_adequacy=4.0,
            min_literalness=3.75,
            min_entity_number_preservation=4.0,
            min_confidence=0.55,
            extra_instruction="Queue small surgical fixes; do not rewrite broad alignment failures.",
        ),
        Recipe(
            name="adversarial_audit",
            judge_profile="adversarial",
            min_adequacy=4.25,
            min_literalness=4.0,
            min_entity_number_preservation=4.25,
            min_confidence=0.65,
            extra_instruction="Be skeptical of synthetic templates, copied text, and target_neg contamination.",
        ),
    ]


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=str(DEFAULT_INPUT))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--prefix", default="codex_gepa_tournament")
    ap.add_argument("--command", default=DEFAULT_CODEX_COMMAND)
    ap.add_argument("--prompt-mode", choices=["stdin", "arg", "file"], default="stdin")
    ap.add_argument("--python-bin", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start-index", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--recipes-json", default="", help="JSON file with an array of recipe objects.")
    ap.add_argument("--only-recipe", action="append", default=[], help="Run only matching recipe name; repeatable.")
    ap.add_argument("--mock-decision", choices=["keep", "drop", "rewrite", "review"], default="")
    ap.add_argument("--skip-quality", action="store_true")
    ap.add_argument("--run-reflection", action="store_true")
    ap.add_argument("--stage-a-total-steps", type=int, default=4000)
    ap.add_argument("--stage-a-save-every", type=int, default=1000)
    ap.add_argument("--on-error", choices=["review", "drop", "keep"], default="review")
    return ap.parse_args()


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _resolve(path_text: str | Path) -> Path:
    path = Path(str(path_text).strip())
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except Exception:
        return str(path)


def _python_bin(args: argparse.Namespace) -> str:
    if str(args.python_bin).strip():
        return str(_resolve(args.python_bin))
    rocm_python = PROJECT_ROOT / ".venv_rocm" / "bin" / "python"
    if rocm_python.is_file():
        return str(rocm_python)
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    return "python3"


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _count_jsonl(path: Path) -> int:
    if not path.is_file():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def _load_recipes(args: argparse.Namespace) -> list[Recipe]:
    if args.recipes_json:
        raw = _read_json(_resolve(args.recipes_json))
        if not isinstance(raw, list):
            raise RuntimeError("--recipes-json must contain an array")
        recipes = [Recipe(**item) for item in raw]
    else:
        recipes = _default_recipes()
    allow = {str(item) for item in args.only_recipe}
    if allow:
        recipes = [recipe for recipe in recipes if recipe.name in allow]
    if not recipes:
        raise RuntimeError("no recipes selected")
    seen: set[str] = set()
    for recipe in recipes:
        if recipe.name in seen:
            raise RuntimeError(f"duplicate recipe name: {recipe.name}")
        seen.add(recipe.name)
    return recipes


def _run_subprocess(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="")
    if completed.returncode != 0:
        raise RuntimeError(f"command failed with code {completed.returncode}: {shlex.join(cmd)}")
    return completed


def _run_filter(
    *,
    args: argparse.Namespace,
    recipe: Recipe,
    input_path: Path,
    recipe_dir: Path,
) -> dict[str, Any]:
    prefix = recipe.name
    cmd = [
        _python_bin(args),
        str(FILTER_SCRIPT),
        "--input",
        str(input_path),
        "--out-dir",
        str(recipe_dir),
        "--prefix",
        prefix,
        "--prompt-mode",
        str(args.prompt_mode),
        "--judge-profile",
        recipe.judge_profile,
        "--rewrite-mode",
        recipe.rewrite_mode,
        "--min-adequacy",
        str(recipe.min_adequacy),
        "--min-literalness",
        str(recipe.min_literalness),
        "--min-entity-number-preservation",
        str(recipe.min_entity_number_preservation),
        "--min-confidence",
        str(recipe.min_confidence),
        "--on-error",
        str(args.on_error),
    ]
    if recipe.extra_instruction:
        cmd.extend(["--extra-instruction", recipe.extra_instruction])
    if int(args.limit) > 0:
        cmd.extend(["--limit", str(int(args.limit))])
    if int(args.start_index) > 0:
        cmd.extend(["--start-index", str(int(args.start_index))])
    if args.resume:
        cmd.append("--resume")
    if args.mock_decision:
        cmd.extend(["--mock-decision", str(args.mock_decision)])
    else:
        cmd.extend(["--command", str(args.command)])

    print(f"[tournament] filter recipe={recipe.name}")
    _run_subprocess(cmd, cwd=PROJECT_ROOT)
    summary_path = recipe_dir / f"{prefix}.summary.json"
    if not summary_path.is_file():
        raise RuntimeError(f"filter summary missing for {recipe.name}: {summary_path}")
    return _read_json(summary_path)


def _score_dataset(
    *,
    args: argparse.Namespace,
    recipe: Recipe,
    recipe_dir: Path,
    filtered_path: Path,
) -> dict[str, Any]:
    if args.skip_quality or _count_jsonl(filtered_path) == 0:
        return {}
    qa_dir = recipe_dir / "quality"
    prefix = f"{recipe.name}.quality"
    cmd = [
        _python_bin(args),
        str(SCORE_SCRIPT),
        str(filtered_path),
        "--out-dir",
        str(qa_dir),
        "--prefix",
        prefix,
    ]
    print(f"[tournament] quality recipe={recipe.name}")
    _run_subprocess(cmd, cwd=PROJECT_ROOT)
    quality_path = qa_dir / f"{prefix}.json"
    data = _read_json(quality_path)
    datasets = data.get("datasets", []) if isinstance(data, dict) else []
    if not datasets:
        return {}
    return datasets[0]


def _score_value(report: dict[str, Any], key: str) -> float:
    scores = report.get("scores", {}) if isinstance(report.get("scores"), dict) else {}
    try:
        return float(scores.get(key, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _weighted_score(row: dict[str, Any]) -> float:
    processed = max(1, int(row.get("processed_rows", 0) or 0))
    keep_ratio = float(row.get("keep_rows", 0) or 0) / processed
    review_ratio = float(row.get("review_rows", 0) or 0) / processed
    report = row.get("quality_report", {}) if isinstance(row.get("quality_report"), dict) else {}
    external = _score_value(report, "external_match")
    alignment = _score_value(report, "alignment_quality")
    gold = _score_value(report, "gold_similarity")
    diversity = _score_value(report, "diversity")
    indomain = _score_value(report, "indomain_match")
    retained = 100.0 * keep_ratio
    review_penalty = 100.0 * review_ratio
    score = (
        0.34 * external
        + 0.24 * alignment
        + 0.16 * gold
        + 0.10 * diversity
        + 0.06 * indomain
        + 0.10 * retained
        - 0.08 * review_penalty
    )
    return round(score, 4)


def _objective_vector(row: dict[str, Any]) -> dict[str, float]:
    processed = max(1, int(row.get("processed_rows", 0) or 0))
    report = row.get("quality_report", {}) if isinstance(row.get("quality_report"), dict) else {}
    return {
        "weighted": float(row.get("weighted_score", 0.0) or 0.0),
        "external": _score_value(report, "external_match"),
        "alignment": _score_value(report, "alignment_quality"),
        "gold": _score_value(report, "gold_similarity"),
        "keep_ratio": float(row.get("keep_rows", 0) or 0) / processed,
    }


def _dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_vec = _objective_vector(left)
    right_vec = _objective_vector(right)
    better_or_equal = all(left_vec[key] >= right_vec[key] for key in left_vec)
    strictly_better = any(left_vec[key] > right_vec[key] for key in left_vec)
    return better_or_equal and strictly_better


def _mark_pareto(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row["pareto_frontier"] = not any(
            _dominates(other, row) for other in rows if other["recipe_name"] != row["recipe_name"]
        )


def _add_elo(rows: list[dict[str, Any]]) -> None:
    ratings = {row["recipe_name"]: 1000.0 for row in rows}
    k_factor = 32.0
    for left in rows:
        for right in rows:
            if left["recipe_name"] >= right["recipe_name"]:
                continue
            left_rating = ratings[left["recipe_name"]]
            right_rating = ratings[right["recipe_name"]]
            expected_left = 1.0 / (1.0 + 10.0 ** ((right_rating - left_rating) / 400.0))
            left_score = float(left["weighted_score"])
            right_score = float(right["weighted_score"])
            if abs(left_score - right_score) < 1e-9:
                actual_left = 0.5
            else:
                actual_left = 1.0 if left_score > right_score else 0.0
            ratings[left["recipe_name"]] = left_rating + k_factor * (actual_left - expected_left)
            ratings[right["recipe_name"]] = right_rating + k_factor * ((1.0 - actual_left) - (1.0 - expected_left))
    for row in rows:
        row["elo"] = round(ratings[row["recipe_name"]], 2)


def _result_row(recipe: Recipe, filter_summary: dict[str, Any], quality_report: dict[str, Any]) -> dict[str, Any]:
    route_counts = filter_summary.get("route_counts", {}) if isinstance(filter_summary.get("route_counts"), dict) else {}
    outputs = filter_summary.get("outputs", {}) if isinstance(filter_summary.get("outputs"), dict) else {}
    row = {
        "recipe_name": recipe.name,
        "judge_profile": recipe.judge_profile,
        "rewrite_mode": recipe.rewrite_mode,
        "min_adequacy": recipe.min_adequacy,
        "min_literalness": recipe.min_literalness,
        "min_entity_number_preservation": recipe.min_entity_number_preservation,
        "min_confidence": recipe.min_confidence,
        "processed_rows": int(filter_summary.get("processed_rows", 0) or 0),
        "keep_rows": int(route_counts.get("keep", 0) or 0),
        "drop_rows": int(route_counts.get("drop", 0) or 0),
        "review_rows": int(route_counts.get("review", 0) or 0),
        "filtered_path": outputs.get("filtered", ""),
        "receipts_path": outputs.get("receipts", ""),
        "summary_path": outputs.get("summary_json", ""),
        "quality_report": quality_report,
    }
    row["weighted_score"] = _weighted_score(row)
    return row


def _flat_score_row(row: dict[str, Any]) -> dict[str, Any]:
    report = row.get("quality_report", {}) if isinstance(row.get("quality_report"), dict) else {}
    return {
        "recipe_name": row["recipe_name"],
        "judge_profile": row["judge_profile"],
        "weighted_score": row["weighted_score"],
        "elo": row.get("elo", ""),
        "pareto_frontier": int(bool(row.get("pareto_frontier"))),
        "processed_rows": row["processed_rows"],
        "keep_rows": row["keep_rows"],
        "drop_rows": row["drop_rows"],
        "review_rows": row["review_rows"],
        "overall": _score_value(report, "overall"),
        "external_match": _score_value(report, "external_match"),
        "alignment_quality": _score_value(report, "alignment_quality"),
        "gold_similarity": _score_value(report, "gold_similarity"),
        "diversity": _score_value(report, "diversity"),
        "indomain_match": _score_value(report, "indomain_match"),
        "filtered_path": row["filtered_path"],
    }


def _write_scoreboard(path: Path, rows: list[dict[str, Any]], champion: dict[str, Any] | None) -> None:
    lines = [
        "# Codex GEPA Translation Judge Tournament",
        "",
        f"Generated: {_now_utc()}",
        "",
    ]
    if champion:
        lines.extend(
            [
                "## Champion",
                "",
                f"- recipe: `{champion['recipe_name']}`",
                f"- weighted_score: `{champion['weighted_score']}`",
                f"- filtered_path: `{champion['filtered_path']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Scoreboard",
            "",
            "| recipe | profile | weighted | elo | pareto | keep/drop/review | external | alignment | gold | diversity | filtered |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        flat = _flat_score_row(row)
        counts = f"{flat['keep_rows']}/{flat['drop_rows']}/{flat['review_rows']}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(flat["recipe_name"]),
                    str(flat["judge_profile"]),
                    str(flat["weighted_score"]),
                    str(flat["elo"]),
                    str(flat["pareto_frontier"]),
                    counts,
                    str(round(float(flat["external_match"]), 4)),
                    str(round(float(flat["alignment_quality"]), 4)),
                    str(round(float(flat["gold_similarity"]), 4)),
                    str(round(float(flat["diversity"]), 4)),
                    f"`{flat['filtered_path']}`",
                ]
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stage_a_plan(champion: dict[str, Any], *, args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    filtered_path = _resolve(str(champion["filtered_path"]))
    row_count = _count_jsonl(filtered_path)
    tag = f"{args.prefix}_{champion['recipe_name']}"
    cmd = [
        _python_bin(args),
        "projects/distillation/translation/pipeline/run_stage_a_gold_shard_grid.py",
        "--sizes",
        str(row_count),
        "--dataset",
        f"{row_count}={_safe_rel(filtered_path)}",
        "--tag",
        tag,
        "--total-steps",
        str(int(args.stage_a_total_steps)),
        "--sft-steps",
        str(int(args.stage_a_total_steps)),
        "--save-every",
        str(int(args.stage_a_save_every)),
    ]
    plan = {
        "champion_recipe": champion["recipe_name"],
        "filtered_path": _safe_rel(filtered_path),
        "rows": row_count,
        "plan_command": shlex.join(cmd),
        "launch_command": shlex.join([*cmd, "--launch"]),
    }
    plan_path = out_dir / f"{args.prefix}.stage_a_plan.json"
    _write_json(plan_path, plan)
    shell_path = out_dir / f"{args.prefix}.stage_a_plan.sh"
    shell_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"cd {shlex.quote(str(PROJECT_ROOT))}\n"
        f"{plan['launch_command']}\n",
        encoding="utf-8",
    )
    plan["plan_json"] = _safe_rel(plan_path)
    plan["plan_shell"] = _safe_rel(shell_path)
    return plan


def _reflection_prompt(rows: list[dict[str, Any]], champion: dict[str, Any] | None) -> str:
    compact_rows = [_flat_score_row(row) for row in rows]
    recipe_schema = {
        "name": "short_snake_case",
        "judge_profile": "balanced|strict_literal|entity_guard|external_wmt|rewrite_surgeon|adversarial",
        "rewrite_mode": "queue",
        "min_adequacy": 4.0,
        "min_literalness": 3.75,
        "min_entity_number_preservation": 4.25,
        "min_confidence": 0.60,
        "extra_instruction": "one precise mutation",
    }
    return (
        "You are evolving EN<->ES data-filter recipes for a Gemma 1B translation distillation student.\n"
        "Given this tournament scoreboard, propose the next generation of judge/filter recipes that should improve "
        "external WMT-like generalization without destroying indomain competence.\n"
        "Prefer concrete mutations: stricter entity handling, external-reference style, rewrite policy, diversity, "
        "or synthetic-template rejection. Return exactly JSON with key next_generation_recipes.\n\n"
        f"Current champion: {json.dumps(champion or {}, ensure_ascii=False, indent=2)}\n\n"
        f"Scoreboard: {json.dumps(compact_rows, ensure_ascii=False, indent=2)}\n\n"
        f"Recipe schema: {json.dumps(recipe_schema, ensure_ascii=False, indent=2)}\n"
    )


def _call_reflection(
    *,
    args: argparse.Namespace,
    prompt: str,
    out_dir: Path,
) -> dict[str, str]:
    prompt_path = out_dir / f"{args.prefix}.reflection_prompt.md"
    response_path = out_dir / f"{args.prefix}.reflection_response.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    argv = [
        item.replace("{prompt_file}", str(prompt_path)).replace("{response_file}", str(response_path))
        for item in shlex.split(str(args.command))
    ]
    input_text: str | None = None
    if args.prompt_mode == "stdin":
        input_text = prompt
    elif args.prompt_mode == "arg":
        replaced = False
        next_argv: list[str] = []
        for item in argv:
            if "{prompt}" in item:
                next_argv.append(item.replace("{prompt}", prompt))
                replaced = True
            else:
                next_argv.append(item)
        argv = next_argv if replaced else [*argv, prompt]
    else:
        if not any("{prompt_file}" in item for item in shlex.split(str(args.command))):
            argv.append(str(prompt_path))
    completed = subprocess.run(
        argv,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    raw = completed.stdout or ""
    if response_path.is_file() and response_path.read_text(encoding="utf-8").strip():
        raw = response_path.read_text(encoding="utf-8")
    stderr_path = out_dir / f"{args.prefix}.reflection_stderr.txt"
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"reflection command failed with code {completed.returncode}: {completed.stderr}")
    response_path.write_text(raw, encoding="utf-8")
    return {
        "prompt": _safe_rel(prompt_path),
        "response": _safe_rel(response_path),
        "stderr": _safe_rel(stderr_path),
    }


def main() -> int:
    args = _parse_args()
    input_path = _resolve(str(args.input))
    out_dir = _resolve(str(args.out_dir)) / str(args.prefix)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not input_path.is_file():
        raise RuntimeError(f"input dataset not found: {input_path}")
    if not FILTER_SCRIPT.is_file():
        raise RuntimeError(f"filter script not found: {FILTER_SCRIPT}")
    if not SCORE_SCRIPT.is_file():
        raise RuntimeError(f"score script not found: {SCORE_SCRIPT}")

    recipes = _load_recipes(args)
    recipe_manifest_path = out_dir / f"{args.prefix}.recipes.json"
    _write_json(recipe_manifest_path, [asdict(recipe) for recipe in recipes])

    rows: list[dict[str, Any]] = []
    for recipe in recipes:
        recipe_dir = out_dir / recipe.name
        recipe_dir.mkdir(parents=True, exist_ok=True)
        filter_summary = _run_filter(args=args, recipe=recipe, input_path=input_path, recipe_dir=recipe_dir)
        outputs = filter_summary.get("outputs", {}) if isinstance(filter_summary.get("outputs"), dict) else {}
        filtered_path = _resolve(str(outputs.get("filtered", "")))
        quality_report = _score_dataset(args=args, recipe=recipe, recipe_dir=recipe_dir, filtered_path=filtered_path)
        rows.append(_result_row(recipe, filter_summary, quality_report))

    _mark_pareto(rows)
    _add_elo(rows)
    rows.sort(key=lambda row: (float(row["weighted_score"]), float(row.get("elo", 0.0))), reverse=True)
    champion = rows[0] if rows else None
    flat_rows = [_flat_score_row(row) for row in rows]

    csv_path = out_dir / f"{args.prefix}.scoreboard.csv"
    _write_csv(
        csv_path,
        flat_rows,
        [
            "recipe_name",
            "judge_profile",
            "weighted_score",
            "elo",
            "pareto_frontier",
            "processed_rows",
            "keep_rows",
            "drop_rows",
            "review_rows",
            "overall",
            "external_match",
            "alignment_quality",
            "gold_similarity",
            "diversity",
            "indomain_match",
            "filtered_path",
        ],
    )
    scoreboard_md = out_dir / f"{args.prefix}.scoreboard.md"
    _write_scoreboard(scoreboard_md, rows, champion)
    reflection_prompt = _reflection_prompt(rows, champion)
    reflection_prompt_path = out_dir / f"{args.prefix}.reflection_prompt.md"
    reflection_prompt_path.write_text(reflection_prompt, encoding="utf-8")
    reflection_artifacts: dict[str, str] = {"prompt": _safe_rel(reflection_prompt_path)}
    if args.run_reflection and not args.mock_decision:
        reflection_artifacts = _call_reflection(args=args, prompt=reflection_prompt, out_dir=out_dir)

    stage_a_plan = _stage_a_plan(champion, args=args, out_dir=out_dir) if champion else {}
    manifest = {
        "generated_utc": _now_utc(),
        "builder": _safe_rel(Path(__file__)),
        "input": _safe_rel(input_path),
        "out_dir": _safe_rel(out_dir),
        "prefix": str(args.prefix),
        "limit": int(args.limit),
        "start_index": int(args.start_index),
        "recipes": [asdict(recipe) for recipe in recipes],
        "results": rows,
        "champion": champion,
        "scoreboard_csv": _safe_rel(csv_path),
        "scoreboard_md": _safe_rel(scoreboard_md),
        "recipes_json": _safe_rel(recipe_manifest_path),
        "reflection": reflection_artifacts,
        "stage_a_plan": stage_a_plan,
    }
    manifest_path = out_dir / f"{args.prefix}.manifest.json"
    _write_json(manifest_path, manifest)

    if champion:
        print(
            "[tournament] "
            f"champion={champion['recipe_name']} "
            f"weighted={champion['weighted_score']} "
            f"filtered={champion['filtered_path']}"
        )
    print(f"[tournament] scoreboard={_safe_rel(scoreboard_md)}")
    print(f"[tournament] manifest={_safe_rel(manifest_path)}")
    if stage_a_plan:
        print(f"[tournament] stage_a_plan={stage_a_plan['plan_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
