"""Write contract.json for iteration 2 once, before any arm runs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ['../matched80-v1/run.py', '../matched80-v1/contract.json', '../BITS_PROMOTION.md', 'run.py', 'test_run.py']
CONTRACT = {
    'schema': 'gamma.matched80.contract.v2',
    'frozen_at': None,
    'parent_commit': None,
    'goals': 'v2:2a/2b representation, Track A development optimization; candidate source for BITS joint80 slots',
    'population': '80 compact sources and qualification evidence exactly as pinned by ../matched80-v1/contract.json (verified on load).',
    'why_compact_only': 'In matched80-v1 every joint arm chose compact source for all 80 problems; canonical arms were never competitive. The polish step still lets either variant win per problem.',
    'arms': {'fixed': [f'fixed-{r}-{w}' for r in ('span', 'hybrid') for w in (12, 48, 192)], 'snapshots': [128, 256], 'polish': ['polish-128', 'polish-256']},
    'candidate_sources': {
        'span': 'scale-v2 proposals() in scale-v2 order (span-count ranking), retired entries excluded; identical to scale-v2 learn().',
        'hybrid': 'Same mined order for the first 3/4 of the shortlist; the last 1/4 holds designed compact pieces (matched80-v1 pool) not already in that head, ranked by the matched80-v1 estimator; unused designed slots fall back to mined order.',
    },
    'admission': 'matched80-v1 learn() (scale-v2 learn with injected candidates): measured exact gain, reclaim, and 3 x 4 complete-dictionary swaps per budget.',
    'fixed_bounds': {'search_seconds_per_arm': 1800, 'max_trials_by_shortlist': {'12': 2200, '48': 8800, '192': 35200}},
    'bounds_note': 'Trial caps scale with shortlist width so each width gets the same trials per shortlist slot as scale-v2. The 1800 s cap is a safety limit; an arm reaching it is flagged.',
    'polish_bounds': {'rounds_per_start': 4, 'trials_per_start': 1200, 'seconds_per_start': 90, 'addition_shortlist': 12, 'removal_shortlist': 4,
                      'pair_addition_shortlist': 6, 'pair_removal_sets': 3},
    'polish_rule': 'For each size, start from the fixed arm with the fewest selections (then package bytes, then name) and run joint-v1 improve() with mined proposals; the start may not be lost.',
    'random_seeds': 'None; deterministic.',
    'codec_and_scoring': 'As matched80-v1: 96-entry charged ASCII fallback, LTD1/LTV1 with 41-byte headers, canonical-codec verification of every packet, lexicographic coverage then selections then package bytes.',
    'predictions': [
        'Q1: span-12 reproduces the stored scale-v2 compact results exactly (10,155 at 128, 6,413 at 256).',
        'Q2: wider shortlists use fewer selections than span-12 at each size.',
        'Q3: hybrid uses no more selections than span at the same shortlist width.',
    ],
    'promotion': 'BITS_PROMOTION.md decides publication: a joint80 slot is replaced only by at least 2% fewer selections (8-bit <= 6,284; 7-bit <= 9,951) with package bytes no more than 5% above live (8-bit <= 12,370; 7-bit <= 13,652), plus a verified guide package and passing BITS checks.',
    'out_of_scope': ['six-bit slots (separate capacity experiment)', 'readable-policy slots', 'other cohorts', 'BITS changes in this commit'],
}


def main():
    out = ROOT / 'contract.json'
    if out.exists():
        raise SystemExit('refusing to overwrite contract.json')
    import subprocess, datetime
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
    contract = dict(CONTRACT, frozen_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'), parent_commit=head,
                    inputs={rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in INPUTS})
    out.write_text(json.dumps(contract, indent=2) + '\n')
    print(f"pinned {len(INPUTS)} inputs at {contract['frozen_at']} on parent {head[:9]}")


if __name__ == '__main__':
    main()
