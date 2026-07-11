#!/usr/bin/env python3
"""Train and apply a reference-free selector for translation candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import sacrebleu
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCORE_KEYS = ("current_model_scores", "specialist_model_scores")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _load_rows(path: Path, *, require_references: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: expected a JSON object")
            candidates = row.get("candidates")
            sources = row.get("candidate_sources")
            if not isinstance(candidates, list) or len(candidates) != 2:
                raise RuntimeError(f"{path}:{line_number}: exactly two candidates are required")
            if not isinstance(sources, list) or len(sources) != 2:
                raise RuntimeError(f"{path}:{line_number}: exactly two candidate sources are required")
            if any(not _safe_text(value) for value in candidates):
                raise RuntimeError(f"{path}:{line_number}: empty candidate")
            if require_references and not _safe_text(row.get("target_pos")):
                raise RuntimeError(f"{path}:{line_number}: training reference is required")
            rows.append(row)
    if not rows:
        raise RuntimeError(f"No candidate rows found in {path}")
    expected_sources = list(rows[0]["candidate_sources"])
    for row_index, row in enumerate(rows, start=1):
        if list(row["candidate_sources"]) != expected_sources:
            raise RuntimeError(f"Candidate source order changed at row {row_index}")
    return rows


def _load_training_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    expected_sources: list[str] | None = None
    for path in paths:
        input_rows = _load_rows(path, require_references=True)
        sources = list(input_rows[0]["candidate_sources"])
        if expected_sources is None:
            expected_sources = sources
        elif sources != expected_sources:
            raise RuntimeError(f"Candidate source order differs across training inputs: {path}")
        for row in input_rows:
            identity = (
                _safe_text(row.get("pair")),
                _safe_text(row.get("source")),
                _safe_text(row.get("target_pos")),
            )
            if identity in seen:
                raise RuntimeError(f"Duplicate training row across selector inputs: {identity[1][:80]}")
            seen.add(identity)
            rows.append(row)
    return rows


def _score_entries(row: dict[str, Any], key: str) -> list[dict[str, Any]]:
    values = row.get(key)
    if not isinstance(values, list) or len(values) != 2:
        raise RuntimeError(f"Missing two-candidate score key {key!r}")
    for value in values:
        if not isinstance(value, dict) or "mean_logprob" not in value or "token_count" not in value:
            raise RuntimeError(f"Invalid score entry under {key!r}")
    return values


def _numeric_error(source: str, candidate: str) -> int:
    source_numbers = Counter(NUMBER_RE.findall(source))
    candidate_numbers = Counter(NUMBER_RE.findall(candidate))
    return sum((source_numbers - candidate_numbers).values()) + sum(
        (candidate_numbers - source_numbers).values()
    )


def _feature_names(score_keys: tuple[str, ...]) -> list[str]:
    names: list[str] = []
    for key in score_keys:
        names.extend((f"{key}_candidate0_mean", f"{key}_candidate1_mean", f"{key}_gap"))
    return [
        *names,
        "score_gap_product",
        "score_gap_disagreement",
        "candidate_token_log_ratio",
        "candidate_char_log_ratio",
        "candidate_word_log_ratio",
        "candidate_similarity",
        "numeric_error_delta",
        "source_char_log",
    ]


def _feature_vector(row: dict[str, Any], score_keys: tuple[str, ...]) -> list[float]:
    candidates = [_safe_text(value) for value in row["candidates"]]
    score_features: list[float] = []
    gaps: list[float] = []
    token_counts: list[list[float]] = []
    for key in score_keys:
        scores = _score_entries(row, key)
        means = [float(score["mean_logprob"]) for score in scores]
        counts = [float(score["token_count"]) for score in scores]
        gap = means[1] - means[0]
        score_features.extend((means[0], means[1], gap))
        gaps.append(gap)
        token_counts.append(counts)
    average_counts = [
        sum(counts[index] for counts in token_counts) / len(token_counts)
        for index in range(2)
    ]
    source = _safe_text(row.get("source"))
    return [
        *score_features,
        math.prod(gaps),
        max(gaps) - min(gaps),
        math.log((average_counts[1] + 1.0) / (average_counts[0] + 1.0)),
        math.log((len(candidates[1]) + 1.0) / (len(candidates[0]) + 1.0)),
        math.log((len(candidates[1].split()) + 1.0) / (len(candidates[0].split()) + 1.0)),
        SequenceMatcher(a=candidates[0], b=candidates[1], autojunk=False).ratio(),
        float(_numeric_error(source, candidates[0]) - _numeric_error(source, candidates[1])),
        math.log1p(len(source)),
    ]


def _expanded_feature_names(names: list[str], expansion: str) -> list[str]:
    if expansion == "linear":
        return list(names)
    if expansion != "quadratic":
        raise RuntimeError(f"Unknown feature expansion: {expansion}")
    output = list(names)
    output.extend(f"{name}^2" for name in names)
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            output.append(f"{names[left]}*{names[right]}")
    return output


def _expand_feature_vector(values: list[float], expansion: str) -> list[float]:
    if expansion == "linear":
        return list(values)
    if expansion != "quadratic":
        raise RuntimeError(f"Unknown feature expansion: {expansion}")
    output = list(values)
    output.extend(value * value for value in values)
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            output.append(values[left] * values[right])
    return output


def _sentence_chrf_delta(row: dict[str, Any]) -> float:
    reference = _safe_text(row["target_pos"])
    candidates = [_safe_text(value) for value in row["candidates"]]
    metric = sacrebleu.metrics.CHRF()
    first = float(metric.sentence_score(candidates[0], [reference]).score)
    second = float(metric.sentence_score(candidates[1], [reference]).score)
    return second - first


def _fit_ridge(
    features: list[list[float]],
    targets: list[float],
    regularization: float,
) -> dict[str, Any]:
    if not features or len(features) != len(targets):
        raise RuntimeError("Ridge training requires aligned non-empty features and targets")
    matrix = torch.tensor(features, dtype=torch.float64)
    target = torch.tensor(targets, dtype=torch.float64)
    means = matrix.mean(dim=0)
    scales = matrix.std(dim=0, unbiased=False)
    scales = torch.where(scales > 1e-12, scales, torch.ones_like(scales))
    normalized = (matrix - means) / scales
    design = torch.cat((normalized, torch.ones((normalized.shape[0], 1), dtype=torch.float64)), dim=1)
    penalty = torch.eye(design.shape[1], dtype=torch.float64) * (
        float(regularization) * float(design.shape[0])
    )
    penalty[-1, -1] = 0.0
    system = design.T @ design + penalty
    rhs = design.T @ target
    try:
        coefficients = torch.linalg.solve(system, rhs)
    except torch.linalg.LinAlgError:
        coefficients = torch.linalg.lstsq(system, rhs.unsqueeze(1)).solution.squeeze(1)
    return {
        "kind": "linear",
        "means": means.tolist(),
        "scales": scales.tolist(),
        "weights": coefficients[:-1].tolist(),
        "bias": float(coefficients[-1].item()),
        "regularization": float(regularization),
    }


def _fit_weighted_logistic(
    features: list[list[float]],
    targets: list[float],
    regularization: float,
) -> dict[str, Any]:
    if not features or len(features) != len(targets):
        raise RuntimeError("Logistic training requires aligned non-empty features and targets")
    matrix = torch.tensor(features, dtype=torch.float64)
    target_delta = torch.tensor(targets, dtype=torch.float64)
    labels = (target_delta > 0.0).to(torch.float64)
    sample_weights = target_delta.abs().clamp_min(0.1)
    means = matrix.mean(dim=0)
    scales = matrix.std(dim=0, unbiased=False)
    scales = torch.where(scales > 1e-12, scales, torch.ones_like(scales))
    normalized = (matrix - means) / scales
    design = torch.cat((normalized, torch.ones((normalized.shape[0], 1), dtype=torch.float64)), dim=1)
    coefficients = torch.zeros(design.shape[1], dtype=torch.float64)
    penalty = torch.eye(design.shape[1], dtype=torch.float64) * (
        float(regularization) * float(design.shape[0])
    )
    penalty[-1, -1] = 0.0
    for _ in range(64):
        logits = design @ coefficients
        probabilities = torch.sigmoid(logits).clamp(1e-9, 1.0 - 1e-9)
        gradient = design.T @ (sample_weights * (probabilities - labels)) + penalty @ coefficients
        curvature = sample_weights * probabilities * (1.0 - probabilities)
        hessian = design.T @ (design * curvature.unsqueeze(1)) + penalty
        hessian = hessian + torch.eye(hessian.shape[0], dtype=torch.float64) * 1e-9
        try:
            update = torch.linalg.solve(hessian, gradient)
        except torch.linalg.LinAlgError:
            update = torch.linalg.lstsq(hessian, gradient.unsqueeze(1)).solution.squeeze(1)
        coefficients = coefficients - update
        if float(update.abs().max().item()) < 1e-8:
            break
    return {
        "kind": "linear",
        "means": means.tolist(),
        "scales": scales.tolist(),
        "weights": coefficients[:-1].tolist(),
        "bias": float(coefficients[-1].item()),
        "regularization": float(regularization),
    }


def _fit_mlp_regression(
    features: list[list[float]],
    targets: list[float],
    regularization: float,
    *,
    hidden_size: int,
    epochs: int,
    learning_rate: float,
    seed: int,
) -> dict[str, Any]:
    if not features or len(features) != len(targets):
        raise RuntimeError("MLP training requires aligned non-empty features and targets")
    if hidden_size <= 0 or epochs <= 0 or learning_rate <= 0.0:
        raise RuntimeError("MLP configuration values must be positive")
    matrix = torch.tensor(features, dtype=torch.float32)
    target = torch.tensor(targets, dtype=torch.float32)
    means = matrix.mean(dim=0)
    scales = matrix.std(dim=0, unbiased=False).clamp_min(1e-6)
    normalized = (matrix - means) / scales
    target_mean = target.mean()
    target_scale = target.std(unbiased=False).clamp_min(1e-6)
    normalized_target = (target - target_mean) / target_scale
    torch.manual_seed(int(seed))
    network = torch.nn.Sequential(
        torch.nn.Linear(normalized.shape[1], hidden_size),
        torch.nn.Tanh(),
        torch.nn.Linear(hidden_size, 1),
    )
    optimizer = torch.optim.Adam(
        network.parameters(),
        lr=float(learning_rate),
        weight_decay=float(regularization),
    )
    for _ in range(int(epochs)):
        optimizer.zero_grad()
        output = network(normalized).squeeze(1)
        loss = torch.nn.functional.smooth_l1_loss(output, normalized_target)
        loss.backward()
        optimizer.step()
    first = network[0]
    second = network[2]
    return {
        "kind": "mlp_regression",
        "means": means.tolist(),
        "scales": scales.tolist(),
        "target_mean": float(target_mean.item()),
        "target_scale": float(target_scale.item()),
        "hidden_size": int(hidden_size),
        "first_weight": first.weight.detach().tolist(),
        "first_bias": first.bias.detach().tolist(),
        "second_weight": second.weight.detach().tolist(),
        "second_bias": second.bias.detach().tolist(),
        "regularization": float(regularization),
        "epochs": int(epochs),
        "learning_rate": float(learning_rate),
        "seed": int(seed),
    }


def _fit_model(
    algorithm: str,
    features: list[list[float]],
    targets: list[float],
    regularization: float,
    *,
    seed: int,
    mlp_hidden: int,
    mlp_epochs: int,
    mlp_learning_rate: float,
) -> dict[str, Any]:
    if algorithm == "ridge_delta":
        return _fit_ridge(features, targets, regularization)
    if algorithm == "weighted_logistic":
        return _fit_weighted_logistic(features, targets, regularization)
    if algorithm == "mlp_regression":
        return _fit_mlp_regression(
            features,
            targets,
            regularization,
            hidden_size=mlp_hidden,
            epochs=mlp_epochs,
            learning_rate=mlp_learning_rate,
            seed=seed,
        )
    raise RuntimeError(f"Unknown selector algorithm: {algorithm}")


def _predict(model: dict[str, Any], features: list[list[float]]) -> list[float]:
    if not features:
        return []
    kind = str(model.get("kind") or "linear")
    if kind == "mlp_regression":
        matrix = torch.tensor(features, dtype=torch.float32)
        means = torch.tensor(model["means"], dtype=torch.float32)
        scales = torch.tensor(model["scales"], dtype=torch.float32)
        first_weight = torch.tensor(model["first_weight"], dtype=torch.float32)
        first_bias = torch.tensor(model["first_bias"], dtype=torch.float32)
        second_weight = torch.tensor(model["second_weight"], dtype=torch.float32)
        second_bias = torch.tensor(model["second_bias"], dtype=torch.float32)
        hidden = torch.tanh(((matrix - means) / scales) @ first_weight.T + first_bias)
        output = hidden @ second_weight.T + second_bias
        return (
            output.squeeze(1) * float(model["target_scale"]) + float(model["target_mean"])
        ).tolist()
    if kind != "linear":
        raise RuntimeError(f"Unknown fitted selector kind: {kind}")
    matrix = torch.tensor(features, dtype=torch.float64)
    means = torch.tensor(model["means"], dtype=torch.float64)
    scales = torch.tensor(model["scales"], dtype=torch.float64)
    weights = torch.tensor(model["weights"], dtype=torch.float64)
    return (((matrix - means) / scales) @ weights + float(model["bias"])).tolist()


def _fold_assignments(rows: list[dict[str, Any]], folds: int, seed: int) -> list[int]:
    if folds < 2 or folds > len(rows):
        raise RuntimeError(f"Invalid fold count {folds} for {len(rows)} rows")
    assignments: list[int] = []
    for row in rows:
        identity = "\0".join(
            (str(seed), _safe_text(row.get("pair")), _safe_text(row.get("source")))
        )
        value = int(hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16], 16)
        assignments.append(value % folds)
    counts = Counter(assignments)
    if len(counts) != folds:
        raise RuntimeError(f"Deterministic fold assignment produced empty folds: {dict(counts)}")
    return assignments


def _corpus_metrics(rows: list[dict[str, Any]], choices: list[int]) -> dict[str, Any]:
    predictions = [_safe_text(row["candidates"][choice]) for row, choice in zip(rows, choices, strict=True)]
    references = [_safe_text(row["target_pos"]) for row in rows]
    return {
        "bleu": float(sacrebleu.corpus_bleu(predictions, [references]).score),
        "chrf": float(sacrebleu.metrics.CHRF().corpus_score(predictions, [references]).score),
        "rows": len(rows),
    }


def _choice_counts(rows: list[dict[str, Any]], choices: list[int]) -> dict[str, int]:
    labels = list(rows[0]["candidate_sources"])
    counts = Counter(labels[choice] for choice in choices)
    return {label: int(counts.get(label, 0)) for label in labels}


def _cross_validate(
    rows: list[dict[str, Any]],
    features: list[list[float]],
    targets: list[float],
    *,
    folds: int,
    seed: int,
    regularization_grid: list[float],
    algorithm: str,
    mlp_hidden: int,
    mlp_epochs: int,
    mlp_learning_rate: float,
) -> tuple[float, list[dict[str, Any]]]:
    assignments = _fold_assignments(rows, folds, seed)
    candidates: list[dict[str, Any]] = []
    for regularization in regularization_grid:
        predictions = [0.0] * len(rows)
        for fold in range(folds):
            train_indices = [index for index, value in enumerate(assignments) if value != fold]
            test_indices = [index for index, value in enumerate(assignments) if value == fold]
            model = _fit_model(
                algorithm,
                [features[index] for index in train_indices],
                [targets[index] for index in train_indices],
                regularization,
                seed=seed * 100 + fold * 100 + mlp_hidden,
                mlp_hidden=mlp_hidden,
                mlp_epochs=mlp_epochs,
                mlp_learning_rate=mlp_learning_rate,
            )
            fold_predictions = _predict(model, [features[index] for index in test_indices])
            for index, prediction in zip(test_indices, fold_predictions, strict=True):
                predictions[index] = prediction
        choices = [1 if value > 0.0 else 0 for value in predictions]
        candidates.append(
            {
                "regularization": float(regularization),
                "metrics": _corpus_metrics(rows, choices),
                "choice_counts": _choice_counts(rows, choices),
            }
        )
    best = max(
        candidates,
        key=lambda item: (
            float(item["metrics"]["chrf"]),
            float(item["metrics"]["bleu"]),
            float(item["regularization"]),
        ),
    )
    return float(best["regularization"]), candidates


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _parse_regularization_grid(value: str) -> list[float]:
    values = sorted({float(item.strip()) for item in value.split(",") if item.strip()})
    if not values or any(item < 0.0 or not math.isfinite(item) for item in values):
        raise RuntimeError(f"Invalid regularization grid: {value!r}")
    return values


def _train(args: argparse.Namespace) -> int:
    input_paths = [Path(value).expanduser().resolve() for value in args.predictions]
    model_path = Path(args.model_out).expanduser().resolve()
    summary_path = Path(args.summary_out).expanduser().resolve()
    rows = _load_training_rows(input_paths)
    score_keys = tuple(args.score_key or DEFAULT_SCORE_KEYS)
    expansion = str(args.feature_expansion)
    names = _expanded_feature_names(_feature_names(score_keys), expansion)
    features = [
        _expand_feature_vector(_feature_vector(row, score_keys), expansion)
        for row in rows
    ]
    targets = [_sentence_chrf_delta(row) for row in rows]
    grid = _parse_regularization_grid(args.regularization_grid)
    algorithm = str(args.algorithm)
    selected_regularization, cv_results = _cross_validate(
        rows,
        features,
        targets,
        folds=int(args.folds),
        seed=int(args.seed),
        regularization_grid=grid,
        algorithm=algorithm,
        mlp_hidden=int(args.mlp_hidden),
        mlp_epochs=int(args.mlp_epochs),
        mlp_learning_rate=float(args.mlp_learning_rate),
    )
    fitted = _fit_model(
        algorithm,
        features,
        targets,
        selected_regularization,
        seed=int(args.seed) * 100 + int(args.mlp_hidden),
        mlp_hidden=int(args.mlp_hidden),
        mlp_epochs=int(args.mlp_epochs),
        mlp_learning_rate=float(args.mlp_learning_rate),
    )
    model = {
        "schema_version": 1,
        "algorithm": algorithm,
        "candidate_sources": list(rows[0]["candidate_sources"]),
        "score_keys": list(score_keys),
        "feature_expansion": expansion,
        "feature_names": names,
        "selector_state": fitted,
        "regularization": fitted["regularization"],
        "training": {
            "inputs": [
                {"path": _project_path(path), "sha256": _sha256_path(path)}
                for path in input_paths
            ],
            "rows": len(rows),
            "folds": int(args.folds),
            "seed": int(args.seed),
            "target": "candidate1_sentence_chrf_minus_candidate0_sentence_chrf",
        },
        "inference_target_access": False,
    }
    if fitted["kind"] == "linear":
        model.update(
            {
                "feature_means": fitted["means"],
                "feature_scales": fitted["scales"],
                "weights": fitted["weights"],
                "bias": fitted["bias"],
            }
        )
    _write_json(model_path, model)
    oracle_choices = [1 if value > 0.0 else 0 for value in targets]
    final_predictions = _predict(fitted, features)
    final_choices = [1 if value > 0.0 else 0 for value in final_predictions]
    selected_cv = next(
        result for result in cv_results if float(result["regularization"]) == selected_regularization
    )
    summary = {
        "algorithm": model["algorithm"],
        "candidate_sources": model["candidate_sources"],
        "score_keys": model["score_keys"],
        "training_input": model["training"],
        "model": {"path": _project_path(model_path), "sha256": _sha256_path(model_path)},
        "regularization_grid": grid,
        "selected_regularization": selected_regularization,
        "cross_validation": cv_results,
        "selected_cross_validation": selected_cv,
        "baselines": {
            str(model["candidate_sources"][0]): _corpus_metrics(rows, [0] * len(rows)),
            str(model["candidate_sources"][1]): _corpus_metrics(rows, [1] * len(rows)),
            "oracle_sentence_chrf": _corpus_metrics(rows, oracle_choices),
            "in_sample_selector": _corpus_metrics(rows, final_choices),
        },
        "in_sample_choice_counts": _choice_counts(rows, final_choices),
        "inference_target_access": False,
    }
    _write_json(summary_path, summary)
    print(
        f"[candidate-selector-train] rows={len(rows)} regularization={selected_regularization:g} "
        f"cv_bleu={selected_cv['metrics']['bleu']:.4f} cv_chrf={selected_cv['metrics']['chrf']:.4f}"
    )
    print(f"[candidate-selector-train] model={model_path}")
    print(f"[candidate-selector-train] summary={summary_path}")
    return 0


def _apply(args: argparse.Namespace) -> int:
    input_paths = [Path(value).expanduser().resolve() for value in args.predictions]
    model_path = Path(args.model).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    summary_path = Path(args.summary_out).expanduser().resolve()
    rows = _load_training_rows(input_paths)
    model = json.loads(model_path.read_text(encoding="utf-8"))
    score_keys = tuple(model["score_keys"])
    expansion = str(model.get("feature_expansion") or "linear")
    expected_sources = list(model["candidate_sources"])
    if list(rows[0]["candidate_sources"]) != expected_sources:
        raise RuntimeError("Application candidate source order does not match the selector model")
    names = _expanded_feature_names(_feature_names(score_keys), expansion)
    if list(model["feature_names"]) != names:
        raise RuntimeError("Selector model feature contract does not match this implementation")
    fitted = model.get("selector_state")
    if not isinstance(fitted, dict):
        fitted = {
            "kind": "linear",
            "means": model["feature_means"],
            "scales": model["feature_scales"],
            "weights": model["weights"],
            "bias": model["bias"],
        }
    features = [
        _expand_feature_vector(_feature_vector(row, score_keys), expansion)
        for row in rows
    ]
    predicted_deltas = _predict(fitted, features)
    choices = [1 if value > 0.0 else 0 for value in predicted_deltas]
    output_rows: list[dict[str, Any]] = []
    for row, choice, predicted_delta in zip(rows, choices, predicted_deltas, strict=True):
        output_rows.append(
            {
                **row,
                "pred": _safe_text(row["candidates"][choice]),
                "selector": {
                    "choice_index": choice,
                    "choice_source": expected_sources[choice],
                    "predicted_chrf_delta": float(predicted_delta),
                    "target_access": False,
                },
            }
        )
    _write_jsonl(out_path, output_rows)
    summary: dict[str, Any] = {
        "algorithm": model["algorithm"],
        "rows": len(rows),
        "candidate_sources": expected_sources,
        "choice_counts": _choice_counts(rows, choices),
        "inputs": [
            {"path": _project_path(path), "sha256": _sha256_path(path)} for path in input_paths
        ],
        "model": {"path": _project_path(model_path), "sha256": _sha256_path(model_path)},
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
        "selection_target_access": False,
    }
    if all(_safe_text(row.get("target_pos")) for row in rows):
        summary["post_selection_metrics"] = _corpus_metrics(rows, choices)
        summary["candidate_baselines"] = {
            expected_sources[0]: _corpus_metrics(rows, [0] * len(rows)),
            expected_sources[1]: _corpus_metrics(rows, [1] * len(rows)),
        }
    _write_json(summary_path, summary)
    metrics = summary.get("post_selection_metrics") or {}
    metric_text = ""
    if metrics:
        metric_text = f" bleu={metrics['bleu']:.4f} chrf={metrics['chrf']:.4f}"
    print(
        f"[candidate-selector-apply] rows={len(rows)} choices={summary['choice_counts']}" + metric_text
    )
    print(f"[candidate-selector-apply] out={out_path}")
    print(f"[candidate-selector-apply] summary={summary_path}")
    return 0


def _ensemble_choices(predictions_by_model: list[list[float]], rule: str) -> list[int]:
    if not predictions_by_model:
        raise RuntimeError("Selector ensemble requires at least one model")
    row_count = len(predictions_by_model[0])
    if any(len(values) != row_count for values in predictions_by_model):
        raise RuntimeError("Selector ensemble prediction counts differ")
    if rule != "unanimous_specialist":
        raise RuntimeError(f"Unknown selector ensemble rule: {rule}")
    return [
        1 if all(values[row_index] > 0.0 for values in predictions_by_model) else 0
        for row_index in range(row_count)
    ]


def _ensemble(args: argparse.Namespace) -> int:
    input_paths = [Path(value).expanduser().resolve() for value in args.predictions]
    model_paths = [Path(value).expanduser().resolve() for value in args.model]
    out_path = Path(args.out).expanduser().resolve()
    summary_path = Path(args.summary_out).expanduser().resolve()
    rows = _load_training_rows(input_paths)
    loaded_models = [json.loads(path.read_text(encoding="utf-8")) for path in model_paths]
    expected_sources = list(loaded_models[0]["candidate_sources"])
    predictions_by_model: list[list[float]] = []
    for model in loaded_models:
        if list(model["candidate_sources"]) != expected_sources:
            raise RuntimeError("Selector ensemble candidate source contracts differ")
        score_keys = tuple(model["score_keys"])
        expansion = str(model.get("feature_expansion") or "linear")
        expected_names = _expanded_feature_names(_feature_names(score_keys), expansion)
        if list(model["feature_names"]) != expected_names:
            raise RuntimeError("Selector ensemble feature contract does not match this implementation")
        state = model.get("selector_state")
        if not isinstance(state, dict):
            state = {
                "kind": "linear",
                "means": model["feature_means"],
                "scales": model["feature_scales"],
                "weights": model["weights"],
                "bias": model["bias"],
            }
        features = [
            _expand_feature_vector(_feature_vector(row, score_keys), expansion)
            for row in rows
        ]
        predictions_by_model.append(_predict(state, features))
    choices = _ensemble_choices(predictions_by_model, str(args.rule))
    output_rows: list[dict[str, Any]] = []
    for row_index, (row, choice) in enumerate(zip(rows, choices, strict=True)):
        deltas = [float(values[row_index]) for values in predictions_by_model]
        output_rows.append(
            {
                **row,
                "pred": _safe_text(row["candidates"][choice]),
                "selector": {
                    "choice_index": choice,
                    "choice_source": expected_sources[choice],
                    "rule": str(args.rule),
                    "model_predicted_chrf_deltas": deltas,
                    "target_access": False,
                },
            }
        )
    _write_jsonl(out_path, output_rows)
    summary = {
        "algorithm": "selector_ensemble",
        "rule": str(args.rule),
        "rows": len(rows),
        "candidate_sources": expected_sources,
        "choice_counts": _choice_counts(rows, choices),
        "inputs": [
            {"path": _project_path(path), "sha256": _sha256_path(path)} for path in input_paths
        ],
        "models": [
            {"path": _project_path(path), "sha256": _sha256_path(path)} for path in model_paths
        ],
        "output": {"path": _project_path(out_path), "sha256": _sha256_path(out_path)},
        "post_selection_metrics": _corpus_metrics(rows, choices),
        "candidate_baselines": {
            expected_sources[0]: _corpus_metrics(rows, [0] * len(rows)),
            expected_sources[1]: _corpus_metrics(rows, [1] * len(rows)),
        },
        "selection_target_access": False,
    }
    _write_json(summary_path, summary)
    metrics = summary["post_selection_metrics"]
    print(
        f"[candidate-selector-ensemble] rows={len(rows)} rule={args.rule} "
        f"choices={summary['choice_counts']} bleu={metrics['bleu']:.4f} chrf={metrics['chrf']:.4f}"
    )
    print(f"[candidate-selector-ensemble] out={out_path}")
    print(f"[candidate-selector-ensemble] summary={summary_path}")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train")
    train.add_argument("--predictions", action="append", required=True)
    train.add_argument("--model-out", required=True)
    train.add_argument("--summary-out", required=True)
    train.add_argument("--score-key", action="append", default=[])
    train.add_argument("--folds", type=int, default=5)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--regularization-grid", default="0.001,0.01,0.1,1,10")
    train.add_argument("--feature-expansion", choices=["linear", "quadratic"], default="linear")
    train.add_argument(
        "--algorithm",
        choices=["ridge_delta", "weighted_logistic", "mlp_regression"],
        default="ridge_delta",
    )
    train.add_argument("--mlp-hidden", type=int, default=8)
    train.add_argument("--mlp-epochs", type=int, default=300)
    train.add_argument("--mlp-learning-rate", type=float, default=0.01)

    apply = subparsers.add_parser("apply")
    apply.add_argument("--predictions", action="append", required=True)
    apply.add_argument("--model", required=True)
    apply.add_argument("--out", required=True)
    apply.add_argument("--summary-out", required=True)

    ensemble = subparsers.add_parser("ensemble")
    ensemble.add_argument("--predictions", action="append", required=True)
    ensemble.add_argument("--model", action="append", required=True)
    ensemble.add_argument("--rule", choices=["unanimous_specialist"], required=True)
    ensemble.add_argument("--out", required=True)
    ensemble.add_argument("--summary-out", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "train":
        return _train(args)
    if args.command == "ensemble":
        return _ensemble(args)
    return _apply(args)


if __name__ == "__main__":
    raise SystemExit(main())
