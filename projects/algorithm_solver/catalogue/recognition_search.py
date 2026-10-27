"""Population-bound recognition, independent of implementation eligibility.

This development mechanism does not create calibration evidence. No solutions,
source locators, availability or language influence its full-population ranking.
"""
import math

from .recognition_inventory import HASH, ID, digest


def population_identity(ordered_ids, document_hashes):
    if (not ordered_ids or len(ordered_ids) != len(document_hashes) or
            len(set(ordered_ids)) != len(ordered_ids) or
            any(not isinstance(pid, str) or not ID.fullmatch(pid) for pid in ordered_ids) or
            any(not isinstance(value, str) or not HASH.fullmatch(value) for value in document_hashes)):
        raise ValueError('exact unique ordered identity/document population required')
    return digest(list(zip(ordered_ids, document_hashes)))


def recognize(scores, ordered_ids, *, document_hashes, population_sha256, policy=None,
              query_truncated=False, index_truncated=False, top_k=10):
    if (len(scores) != len(ordered_ids) or len(scores) < 2 or
            len(set(ordered_ids)) != len(ordered_ids) or type(top_k) is not int or top_k < 1 or
            any(not isinstance(pid, str) or not pid for pid in ordered_ids) or
            any(not math.isfinite(float(score)) for score in scores)):
        raise ValueError('complete unique population and finite scores required')
    if population_identity(ordered_ids, document_hashes) != population_sha256:
        raise ValueError('actual population identity/document binding mismatch')
    ranked = sorted(zip(ordered_ids, map(float, scores)), key=lambda row: (-row[1], row[0]))
    result = {'status': 'abstain', 'reason': 'population_not_calibrated',
        'population_sha256': population_sha256,
        'candidates': [{'problem_id': pid, 'score': score} for pid, score in ranked[:top_k]],
        'searched_population': len(ordered_ids), 'clarification_questions': [],
        'implementation_availability_used': False, 'recognition_qualified': False}
    if query_truncated or index_truncated:
        return dict(result, reason='truncation')
    if policy is None:
        return result
    if not isinstance(policy, dict):
        raise ValueError('explicit calibration policy required')
    if policy.get('population_sha256') != population_sha256:
        raise ValueError('policy population mismatch; recalibration required')
    if policy.get('evidence_class') != 'development-calibration':
        raise ValueError('explicit development calibration evidence class required')
    cosine, margin = policy.get('min_cosine'), policy.get('min_margin')
    if (type(cosine) not in (float, int) or type(margin) not in (float, int) or
            not math.isfinite(cosine) or not math.isfinite(margin) or
            not -1 <= cosine <= 1 or not 0 <= margin <= 2):
        raise ValueError('finite calibrated thresholds required')
    observed_margin = ranked[0][1] - ranked[1][1]
    if observed_margin <= 0:
        return dict(result, reason='ambiguous_tie')
    if ranked[0][1] < cosine or observed_margin < margin:
        return dict(result, reason='calibrated_confidence')
    return dict(result, status='recognized', reason=None, problem_id=ranked[0][0],
                score=ranked[0][1], margin=observed_margin)


def attach_implementation(recognition, lookup):
    """Post-ranking exact identity lookup; no available-neighbor fallback."""
    result = dict(recognition)
    if result['status'] != 'recognized':
        result['implementation'] = None
        return result
    identity = result['problem_id']
    implementation = lookup(identity)
    if (not isinstance(implementation, dict) or
            implementation.get('problem_id', identity) != identity or
            (implementation.get('status') == 'matched' and implementation.get('problem_id') != identity)):
        raise ValueError('implementation lookup substituted or omitted exact identity')
    result['implementation'] = implementation
    return result


def summarize_development(rows):
    """Report retrieval, decision and implementation measures separately."""
    metrics = {}
    for kind in sorted({row['kind'] for row in rows}):
        group = [row for row in rows if row['kind'] == kind]
        labeled = [row for row in group if row.get('expected_ids')]
        def hit(row, k):
            candidates = row['recognition']['candidates'][:k]
            return bool(set(row['expected_ids']) & {c['problem_id'] for c in candidates})
        metrics[kind] = {'queries': len(group), 'target_queries': len(labeled),
            'target_top1': sum(hit(row, 1) for row in labeled),
            'target_top5': sum(hit(row, 5) for row in labeled),
            'correct_recognitions': sum(row['recognition'].get('problem_id') in row['expected_ids']
                and row['recognition']['status'] == 'recognized' for row in labeled),
            'wrong_recognitions': sum(row['recognition']['status'] == 'recognized'
                and row['recognition'].get('problem_id') not in row.get('expected_ids', []) for row in group),
            'abstentions': sum(row['recognition']['status'] != 'recognized' for row in group),
            'implementation_available': sum((row['recognition'].get('implementation') or {}).get('status')
                == 'matched' for row in group)}
    return {'schema': 'gamma.recognition-development-metrics.v1', 'by_kind': metrics,
        'evidence_class': 'development', 'confirmation_opened': False,
        'recognition_qualified': False, 'implementation_availability_is_not_target_recall': True}
