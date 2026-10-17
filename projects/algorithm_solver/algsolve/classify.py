"""Multi-label algorithm-pattern classifier with an explicit "unknown" outcome.

TF-IDF over the statement plus one-vs-rest logistic regression, trained only
on lookup-index entries (solving pools and their aliases/near-duplicates are
already excluded from the index). Labels come from LeetCode tags mapped to
patterns. Up to two patterns are returned; if none clears the threshold the
prediction is "unknown". The threshold is chosen by cross-validation on the
training entries and frozen with the model.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import numpy as np

from .patterns.catalog import PATTERNS, patterns_for_tags
from .records import DERIVED, LANE_ROOT
from .splits import IndexEntry

MODEL_PATH = DERIVED / "classifier.joblib"
METRICS_PATH = LANE_ROOT / "contracts" / "classifier_metrics.json"
MAX_LABELS = 2
LABELS = sorted(PATTERNS)


@dataclass
class Prediction:
    patterns: list[str]            # empty means unknown
    probabilities: dict[str, float]
    seconds: float

    @property
    def unknown(self) -> bool:
        return not self.patterns


def _pipeline():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.pipeline import make_pipeline

    return make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=200_000, sublinear_tf=True),
        OneVsRestClassifier(LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced")),
    )


def _targets(entries: list[IndexEntry]) -> np.ndarray:
    y = np.zeros((len(entries), len(LABELS)), dtype=int)
    for i, entry in enumerate(entries):
        for name in patterns_for_tags(entry.tags):
            y[i, LABELS.index(name)] = 1
    return y


def _select(probabilities: np.ndarray, threshold: float) -> list[int]:
    order = np.argsort(-probabilities)[:MAX_LABELS]
    return [int(i) for i in order if probabilities[i] >= threshold]


def _micro_f1(y: np.ndarray, probs: np.ndarray, threshold: float) -> tuple[float, float]:
    tp = fp = fn = 0
    unknown = 0
    for row_y, row_p in zip(y, probs):
        chosen = set(_select(row_p, threshold))
        truth = set(np.nonzero(row_y)[0])
        unknown += not chosen
        tp += len(chosen & truth)
        fp += len(chosen - truth)
        fn += len(truth - chosen)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return f1, unknown / len(y)


def train(entries: list[IndexEntry], seed: int = 20261017) -> dict:
    import joblib
    from sklearn.model_selection import KFold

    labelled = [e for e in entries if patterns_for_tags(e.tags)]
    texts = [e.statement for e in labelled]
    y = _targets(labelled)
    oof = np.zeros(y.shape, dtype=float)
    for train_idx, test_idx in KFold(n_splits=5, shuffle=True, random_state=seed).split(texts):
        model = _pipeline()
        model.fit([texts[i] for i in train_idx], y[train_idx])
        oof[test_idx] = model.predict_proba([texts[i] for i in test_idx])
    grid = [round(t, 2) for t in np.arange(0.20, 0.91, 0.05)]
    scored = [(t, *_micro_f1(y, oof, t)) for t in grid]
    threshold, f1, unknown_rate = max(scored, key=lambda s: s[1])
    model = _pipeline()
    model.fit(texts, y)
    joblib.dump({"model": model, "labels": LABELS, "threshold": threshold}, MODEL_PATH)
    per_label = {}
    for k, name in enumerate(LABELS):
        support = int(y[:, k].sum())
        chosen = np.array([k in _select(row, threshold) for row in oof])
        tp = int((chosen & (y[:, k] == 1)).sum())
        per_label[name] = {
            "support": support,
            "precision": round(tp / chosen.sum(), 3) if chosen.sum() else None,
            "recall": round(tp / support, 3) if support else None,
        }
    metrics = {
        "trained_on_index_entries": len(labelled),
        "unlabelled_entries_skipped": len(entries) - len(labelled),
        "cv": "5-fold, out-of-fold probabilities",
        "threshold": threshold,
        "cv_micro_f1": round(f1, 4),
        "cv_unknown_rate": round(unknown_rate, 4),
        "threshold_grid": [{"threshold": t, "micro_f1": round(f, 4), "unknown_rate": round(u, 4)} for t, f, u in scored],
        "per_label": per_label,
        "max_labels": MAX_LABELS,
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=1) + "\n")
    return metrics


class Classifier:
    def __init__(self) -> None:
        import joblib

        bundle = joblib.load(MODEL_PATH)
        self.model = bundle["model"]
        self.labels = bundle["labels"]
        self.threshold = bundle["threshold"]

    def predict(self, statement: str) -> Prediction:
        started = time.perf_counter()
        probs = self.model.predict_proba([statement])[0]
        chosen = [self.labels[i] for i in _select(probs, self.threshold)]
        return Prediction(
            patterns=chosen,
            probabilities={self.labels[i]: round(float(p), 4) for i, p in enumerate(probs)},
            seconds=time.perf_counter() - started,
        )
