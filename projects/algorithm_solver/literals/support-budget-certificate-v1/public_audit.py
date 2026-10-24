"""Read only item35 PUBLIC evidence; derive a theorem, not a new trajectory."""
import hashlib
import json
from pathlib import Path

PUBLIC_EVIDENCE = Path(__file__).resolve().parents[1] / 'length-sensitive-fraction-v1/evidence/results.json'


def audit(data):
    assert data['complete'] is True
    assert sorted(a['cohort'] for a in data['arms']) == ['R', 'naming']
    rows = []
    for a in data['arms']:
        c = a['certificate']
        assert a['complete'] and a['fit_problems'] == 300 and a['capacity'] == 256
        assert a['source_bans_pool_q_and_packets_replayed'] is True
        assert c['independent_partition_and_integer_replay'] is True
        assert a['initial_q_all_zero'] is True
        d = c['denominator']
        assert type(d) is int and d > 0
        for v in [c['numerator'], c['top_capacity_numerator'], a['initial_numerator'], *c['path_numerators'].values()]:
            assert type(v) is int
        assert c['top_capacity_numerator'] >= 0
        assert len(c['path_numerators']) == 300
        path_sum = sum(c['path_numerators'].values())
        assert path_sum == c['numerator'] + c['top_capacity_numerator']
        assert c['integer_lower_bound'] == -(-c['numerator'] // d)
        # Since every T_k >=0, the new best-q lower bound cannot exceed ceil(L/D).
        ceiling = -(-path_sum // d)
        zero_ceiling = -(-a['initial_numerator'] // d)
        assert ceiling <= 0 and zero_ceiling <= 0
        rows.append({'cohort': a['cohort'], 'denominator': d,
                     'recorded_best_numerator': c['numerator'],
                     'recorded_top256_numerator': c['top_capacity_numerator'],
                     'recorded_path_sum_numerator': path_sum,
                     'best_q_bound_ceiling_for_every_k': ceiling,
                     'zero_q_bound_for_every_k': zero_ceiling,
                     'two_point_bound_ceiling_for_every_k': max(ceiling, zero_ceiling),
                     'positive_exclusion_possible_at_proposed_q_points': False})
    return {'schema': 'support-budget-public-preflight-v1',
            'status': 'analytical_null_no_private_experiment',
            'scope': 'Each unchanged item35 fixed300 fit population only',
            'support_budget_trajectory_computed': False,
            'support_optimized_q_tested': False, 'rows': rows}


def main():
    if not __debug__:
        raise RuntimeError('Python assertions required')
    raw = PUBLIC_EVIDENCE.read_bytes()
    result = audit(json.loads(raw))
    result['public_evidence_sha256'] = hashlib.sha256(raw).hexdigest()
    result['public_evidence'] = '../length-sensitive-fraction-v1/evidence/results.json'
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
