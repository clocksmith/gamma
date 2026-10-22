"""Write contract.json: the frozen design plus SHA-256 pins of every input. Run once before any arm."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = [
    '../scale-v2/generated/manifest.json', '../scale-v2/qualification/report.json',
    '../scale-v2/qualification-rerun-v1/report.json', '../scale-v2/qualification-rerun-v1/comparison.json',
    '../scale-v2/contract.json', '../scale-v2/search.py', '../clusters-v1/search.py', '../literals.py',
    '../pass2/working/bitpack.py', '../joint-v1/search.py', '../readable-v1/literal_codec.py',
    *[f'../scale-v2/search-v2/{s}-marginal-{n}/{f}' for s in ('canonical', 'compact') for n in (128, 256) for f in ('manifest.json', 'dictionary.json')],
    'designed/build_pool.py', 'designed/pool.json', 'designed/qualify_components.cjs',
    'designed/qualification-mars.json', 'designed/qualification-jupiter.json',
    'labels/extract_labels.py', 'labels/ids.json', 'labels/labels.json', 'run.py', 'test_run.py',
]

CONTRACT = {
    'schema': 'gamma.matched80.contract.v1',
    'frozen_at': '2026-10-21T22:49:07-04:00',
    'parent_commit': '8e9593c3f9eebbfe1b32aa6daa720ca85c6b3933',
    'goals': 'v2:2a/2b representation, Track A development optimization only',
    'population': {'problems': 80, 'ids': 'labels/ids.json', 'styles': ['canonical', 'compact'],
                   'exposure': 'Exposed development: scale-v2 prior60 plus additional20. No protected, reserved or unseen problem is read.'},
    'qualification_receipts': {'stored': '../scale-v2/qualification/report.json', 'rerun': '../scale-v2/qualification-rerun-v1/report.json'},
    'evidence_classes': 'Source correctness rests on the stored receipt and the 2026-10-21 fresh-copy rerun, kept distinct; both must cover every source. This experiment executes no candidate source: every packet must decode, via the canonical codec, to a qualified source hash.',
    'designed_pool': 'designed/pool.json',
    'arms': {
        'fixed': [f'fixed-{p}-{s}-{n}' for p in ('designed', 'mined', 'combined') for s in ('canonical', 'compact') for n in (128, 256)],
        'joint': [f'joint-{p}-{n}' for p in ('designed', 'mined', 'combined') for n in (128, 256)],
        'control': ['control-scale-v2-canonical', 'control-scale-v2-compact'],
    },
    'candidate_generation': {
        'designed': 'Frozen owner-approved pool for the arm style only (86 canonical, 41 compact pieces), each witnessed in at least two problems.',
        'mined': 'scale-v2 proposals(): contiguous spans of 2-4 current entries occurring in at least two distinct problems, at most 160 UTF-8 bytes, never a whole program.',
        'combined': 'Union of designed and mined candidates; each admitted entry keeps its provenance.',
        'joint_mined': 'joint-v1 proposals(): spans of 2-6 parsed parts across both variants, at least two distinct problems.',
        'joint_designed': 'Canonical and compact designed pieces with at least two distinct problem owners across variants.',
    },
    'shortlist_ranking': 'Identical for every pool: occurrences in the joined texts times (current segmentation length - 1); ties by UTF-8 length, then string. Ranking orders the shortlist only; measured exact gain decides admission. This replaces scale-v2 span-count ranking, which applies only to mined spans; the reproduction control reruns scale-v2 unchanged.',
    'admission': 'scale-v2 learn(): admit the shortlisted candidate with the largest measured exact selection gain if positive; reclaim learned entries left unused; at each budget, test 3 lowest-frequency removals x 4 top-ranked additions as complete-dictionary swaps.',
    'fixed_bounds': {'search_seconds_per_arm': 300, 'shortlist': 12, 'max_trials_per_arm': 2200},
    'fixed_budget_note': 'One trajectory per pool and style; the 128- and 256-entry arms are its snapshots and share the 2,200-trial cap, as in scale-v2. Designed-only trajectories may stop below a budget when the pool is exhausted; entries used are reported, never padded.',
    'joint_bounds': {'starts': 'both fixed arms of the same pool and size', 'rounds_per_start': 4, 'trials_per_start': 1200, 'seconds_per_start': 90,
                     'addition_shortlist': 12, 'removal_shortlist': 4, 'pair_addition_shortlist': 6, 'pair_removal_sets': 3},
    'joint_rules': 'Per problem, the canonical or compact source with fewer selections (then fewer bytes) is chosen. Objective: input (selections, then package bytes). The best eligible fixed-source arm of the same pool and size is the incumbent and may not be lost. Inherited fixed-search trials and seconds are disclosed alongside joint trials; joint and fixed arms are not claimed to use equal total computation.',
    'random_seeds': 'None. The search is deterministic; the trial cap is the binding budget. The time cap is a safety limit; any arm reaching it is flagged as machine-dependent.',
    'fallback_alphabet': '96 entries: ASCII U+0020..U+007E plus newline, always present and charged in every arm.',
    'codec': {'encoder': '../pass2/working/bitpack.py', 'verifier': '../readable-v1/literal_codec.py verify_packet',
              'format': 'LTD1 dictionary; LTV1 packets with a 41-byte header, fixed width per arm (7 bits for 128, 8 bits for 256).'},
    'scoring': 'Lexicographic: coverage (programs decoding to their qualified source hash), then total selections, then complete package bytes. No single blended score is reported.',
    'metrics': ['covered_programs', 'total_input_bits', 'selections', 'median_selections', 'p95_selections', 'worst_selections',
                'entries', 'entries_by_provenance', 'dictionary_bytes', 'package_bytes', 'decoder_bytes (shared codec files, constant)',
                'single_character_selection_fraction', 'fallback_character_fraction', 'search_seconds', 'trials', 'peak_rss_bytes'],
    'breakdowns': 'Per arm by difficulty (69 Easy, 9 Medium, 2 Hard) and by LeetCode tag, each tag counting every problem carrying it, plus primary tag by the precedence frozen in labels/extract_labels.py. Small cells are descriptive only.',
    'preparation_costs': 'Reported separately from search: designed-pool building, component qualification (228 checks, Mars and Jupiter), label extraction. Mined candidates are generated inside the search and counted in its trials and seconds.',
    'reproduction_control': 'Unchanged scale-v2 learn() for each style must reproduce the stored marginal-128/256 dictionaries and selections; a mismatch is reported, not hidden.',
    'predictions': [
        'P1: On canonical sources, combined uses no more selections than mined at each size.',
        'P2: Designed-only uses more selections than mined at each size; the difference is the measured cost of a readable-only menu.',
        'P3: Fewer designed entries are admitted in compact combined arms than in canonical combined arms.',
        'P4: Each joint arm uses no more selections than its best fixed arm; the size of any improvement is unknown.',
    ],
    'out_of_scope': ['parameterized macros', 'cursor or editor actions', 'BITS or live dictionary changes', 'six-bit capacity tests (after this experiment)',
                     'protected, reserved or unseen problems', 'human learning', 'autonomous composition'],
    'resource_envelope': {'host': 'Mars (macOS), one worker', 'artifact_cap_bytes': 67108864},
    'promotion': 'Development evidence on 80 exposed problems only. Any gain needs a predeclared matched confirmation and independent review before promotion, publication or BITS export.',
}


def main():
    out = ROOT / 'contract.json'
    if out.exists():
        raise SystemExit('refusing to overwrite contract.json')
    contract = dict(CONTRACT, inputs={rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in INPUTS})
    out.write_text(json.dumps(contract, indent=2) + '\n')
    print(f'pinned {len(INPUTS)} inputs')


if __name__ == '__main__':
    main()
