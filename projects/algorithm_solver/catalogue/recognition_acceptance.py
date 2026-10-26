"""Score a complete frozen cohort; labels never enter recognition or calibration.

Point estimates are not release qualification or population-risk guarantees.
Existing independent-evidence, ambiguity and source-verification gates still apply.
"""
from .empirical_recognition import score_decisions
from ..algsolve.recognition_metrics import wilson


def evaluate(cohort, decisions_by_id):
    ids = [q['id'] for q in cohort]
    if (not ids or len(set(ids)) != len(ids) or
            any(not isinstance(key, str) or not key for key in ids) or
            set(decisions_by_id) != set(ids)):
        raise ValueError('one decision per frozen query required; no missing or extra cases')
    counts = score_decisions(cohort, [decisions_by_id[key] for key in ids])
    tp = counts['correct_accepts']
    fp = counts['wrong_positive_accepts'] + counts['control_accepts']
    positives = counts['positive_count']
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / positives if positives else None
    return dict(counts, true_positives=tp, false_positives=fp,
                false_negatives=positives - tp, precision=precision, recall=recall,
                precision_wilson_95=wilson(tp, tp + fp), recall_wilson_95=wilson(tp, positives),
                meets_99_percent_point_targets=(precision is not None and recall is not None
                    and counts['control_count'] > 0 and precision >= .99 and recall >= .99),
                recognition_qualified=False)
