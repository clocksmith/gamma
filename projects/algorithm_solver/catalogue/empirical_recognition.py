"""Finite-cohort empirical decisions, separate from sound-schema interpretation.

Threshold acceptance is a measured classifier, never a semantic proof. Candidate
availability cannot influence ranking. Evaluation labels never enter decide().
"""
import math


def rank(scores, ids):
    if (len(scores) != len(ids) or len(ids) < 2 or len(set(ids)) != len(ids) or
            any(not isinstance(x, str) for x in ids) or
            any(not math.isfinite(float(s)) for s in scores)):
        raise ValueError('invalid complete competitor scores')
    return sorted(zip(ids, map(float, scores)), key=lambda row: (-row[1], row[0]))


def decide(ranked, policy, service, *, truncated=False):
    """Return qualified metadata and exact scope; no source is opened here."""
    abstain = {'status': 'abstain', 'clarification_questions': [],
               'mode': 'empirical-authored-cohort', 'semantic_proof': False}
    if truncated:
        return dict(abstain, reason='truncated_query_or_index')
    if len(ranked) < 2 or any(not math.isfinite(float(row[1])) for row in ranked):
        raise ValueError('complete finite ranking required')
    c, m = policy['min_cosine'], policy['min_margin']
    if type(c) not in (float, int) or type(m) not in (float, int) or not -1 <= c <= 1 or not 0 <= m <= 2:
        raise ValueError('invalid policy thresholds')
    ident, score = ranked[0]
    margin = score - ranked[1][1]
    # Ties are inherently unresolved even when the configured margin is zero.
    if score < c or margin <= 0 or margin < m:
        return dict(abstain, reason='empirical_confidence_threshold')
    value = service.request(ident, include_source=False)
    if value['status'] != 'matched':
        return dict(abstain, reason='top_identity_not_qualified')
    selected = {}
    for language in ('javascript', 'python'):
        result = service.request(ident, language=language, include_source=False)
        if result['status'] != 'matched' or result.get('consumer_selection', {}).get('status') != 'selected':
            return dict(abstain, reason='both_languages_not_qualified')
        selected[language] = result['consumer_selection']
    return {'status': 'accepted', 'problem_id': ident, 'implementations': selected,
            'clarification_questions': [], 'mode': 'empirical-authored-cohort',
            'semantic_proof': False, 'cosine': score, 'margin': margin,
            'applicability': 'Only the exact returned implementation contracts; identity/applicability inferred empirically, not proven for arbitrary descriptions.'}


def score_decisions(queries, decisions):
    if len(queries) != len(decisions):
        raise ValueError('evaluation length mismatch')
    out = dict(positive_count=0, control_count=0, correct_accepts=0,
               wrong_positive_accepts=0, control_accepts=0, abstentions=0)
    for q, d in zip(queries, decisions):
        positive = q['kind'] == 'positive'
        out['positive_count' if positive else 'control_count'] += 1
        if d['status'] == 'abstain':
            out['abstentions'] += 1
        elif d['status'] != 'accepted':
            raise ValueError('unknown decision status')
        elif not positive:
            out['control_accepts'] += 1
        else:
            expected = q.get('expected_id')
            if expected is None:
                expected_ids = q.get('expected_ids', [])
            else:
                expected_ids = [expected]
            out['correct_accepts' if d['problem_id'] in expected_ids else 'wrong_positive_accepts'] += 1
    return out


def select_policy(results):
    feasible = [r for r in results if r['metrics']['wrong_positive_accepts'] == 0 and r['metrics']['control_accepts'] == 0]
    if not feasible:
        return None
    return min(feasible, key=lambda r: (-r['metrics']['correct_accepts'],
        -r['policy']['min_cosine'], -r['policy']['min_margin'], r['policy']['id']))['policy']
