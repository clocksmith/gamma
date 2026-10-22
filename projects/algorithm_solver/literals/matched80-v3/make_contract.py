"""Write contract.json for iteration 3 once, before any arm runs."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ['../matched80-v1/run.py', '../matched80-v1/contract.json', '../BITS_PROMOTION.md',
          '../matched80-v2/run-v1/polish-128/dictionary.json', '../matched80-v2/run-v1/polish-256/dictionary.json',
          '../matched80-v2/run-v1/polish-128/manifest.json', '../matched80-v1/run-v1/fixed-designed-canonical-128/manifest.json',
          '../matched80-v1/run-v1/fixed-designed-canonical-256/manifest.json', '../matched80-v1/run-v1/fixed-designed-compact-128/manifest.json',
          '../matched80-v1/run-v1/fixed-designed-compact-256/manifest.json', 'units.py', 'run.py', 'test_run.py']
CONTRACT = {
    'schema': 'gamma.matched80.contract.v3',
    'frozen_at': None,
    'parent_commit': None,
    'goals': 'v2:2a compression-first and human-readable policies, kept as separate scorecards; candidate source for BITS joint80 slots',
    'population': '80 compact and 80 canonical sources and qualification evidence exactly as pinned by ../matched80-v1/contract.json (verified on load).',
    'literal_scorecard': {
        'sources': 'The 80 compact sources only: the published BITS joint80 cohort. Every matched80-v1/v2 joint arm chose compact for all 80 problems; evaluating compact only makes each exact trial about 4.6x cheaper.',
        'starts': {'v2polish': '../matched80-v2/run-v1/polish-{size}/dictionary.json (9,910 at 128; 6,360 at 256)',
                   'scalev2': '../scale-v2/search-v2/compact-marginal-{size}/dictionary.json (10,155 at 128; 6,413 at 256, the live 8-bit profile)'},
        'arms': {'wide-<start>-<size>': 'deterministic local search from each start (run.local_search)',
                 'ils-<size>-s<seed>': 'seeded iterated local search from the better wide arm of that size (by selections, then package bytes, then name)'},
        'candidate_source': 'Hybrid additions: the first 3/4 in joint-v1 proposals() span order; the last 1/4 are matched80-v1 designed pieces (canonical and compact) witnessed in at least two problems and not in that head, ranked by the matched80-v1 estimator; unused designed slots fall back to span order.',
        'move': 'Per round: exact deletion harm of every learned entry; exact gain of every addition (capacity relaxed by one entry when full, gain only); the swaps with the highest estimated gain (addition gain minus deletion harm) and the double swaps (two additions, as many lowest-harm removals as capacity needs) with the highest estimate are tested exactly; the best exact (selections, package bytes) improvement is accepted, then unused entries are pruned. A round with no improvement ends the local search.',
        'kick': 'ILS: remove `kick` learned entries sampled uniformly with random.Random(seed) from the sorted learned list, refill greedily with the best exact addition from a `refill_shortlist` hybrid shortlist until full or no addition gains, run the local search, keep the result only if it improves (selections, package bytes) on the incumbent; repeat until the trial cap.',
    },
    'readable_scorecard': {
        'policy': 'readable-units-v1 (units.py): every non-fallback entry is a lexical unit of class name, member, head, tail, operator or indent, witnessed in at least two problems of that style and at most 32 bytes, or (pool units-designed) a matched80-v1 owner-approved designed piece of that style. No mined fragment is admitted; run.py asserts the policy on every final dictionary.',
        'arms': {'readable-<pool>-<style>-<size>': 'pools units and units-designed; styles canonical and compact (fixed style, not joint); sizes 128 and 256 are snapshots of one matched80-v1 learn() trajectory with readable candidates ranked by the matched80-v1 estimator, each then polished by run.local_search with readable candidates only'},
        'baseline': 'matched80-v1 fixed-designed-<style>-<size> (designed-only readable menu): canonical 28,607 / 25,720; compact 11,794 / 11,593 selections',
        'quality_metric': 'token-aligned selection fraction: selections whose start and end both fall on units.tokens() boundaries (names, numbers, strings and multi-character operators are not split)',
    },
    'wide': {'trials': 600000, 'seconds': 5400},
    'ils': {'trials': 400000, 'seconds': 5400, 'seeds': [1, 2, 3, 4, 5], 'kick': {'128': 4, '256': 8}, 'refill_shortlist': 24},
    'neighborhood': {'additions': 96, 'designed_fraction': 0.25, 'swaps': 500, 'pair_additions': 16, 'pair_removals': 8, 'pairs': 150},
    'readable': {'pools': ['units', 'units-designed'], 'styles': ['canonical', 'compact'],
                 'learn': {'shortlist': 48, 'max_trials_per_arm': 8800, 'search_seconds_per_arm': 1800},
                 'polish': {'trials': 100000, 'seconds': 5400}},
    'bounds_note': 'Trial caps bind; seconds are safety limits and any arm reaching one is flagged. Every evaluation, including relaxed-capacity gain measurements and prunes, counts as a trial. Children run with PYTHONHASHSEED=0.',
    'codec_and_scoring': 'As matched80-v1: 96-entry charged ASCII fallback, exact shortest segmentation, LTD1/LTV1 with 41-byte packet headers, canonical-codec verification of every packet, (selections, package bytes) lexicographic. The shared decoder (readable-v1/literal_codec.py, pass2/working/bitpack.py) is unchanged and listed separately.',
    'reporting': 'Every arm: selections, dictionary bytes, packet bytes, package bytes, per-problem min/median/p90/max, per-problem deltas against its reference (literal: live profile of that size, the 7-bit v2 polish-128 and 8-bit scale-v2 compact-marginal-256 manifests; readable: the matched80-v1 designed-only arm of that style and size) with counts better/same/worse and the largest increase, trials, seconds and stop reason. All ILS seeds are reported, with min/median/max.',
    'predictions': [
        'L1: wide-v2polish beats its start at both sizes (< 9,910 at 128; < 6,360 at 256).',
        'L2: the best 8-bit literal arm meets the unchanged 8-bit bar (<= 6,284 selections and <= 12,370 package bytes).',
        'L3: at each size at least 4 of 5 ILS seeds improve on their start, and the seed spread (max - min) is at most 1% of the median.',
        'L4: at each size wide-scalev2 ends within 1% of wide-v2polish.',
        'R1: readable units-designed uses fewer selections than the matched80-v1 designed-only arm at each style and size.',
        'R2: readable units-designed uses no more selections than readable units at each style and size.',
        'R3: readable units-designed has a higher token-aligned selection fraction than the matched80-v1 designed-only arm at each style and size.',
    ],
    'promotion': 'Unchanged BITS_PROMOTION.md. Per size, the candidate is the literal arm (wide or any ILS seed) with the fewest selections, then package bytes, then name; every seed is reported. 8-bit: <= 6,284 selections (2% below 6,413) and <= 12,370 package bytes (5% above 11,781). 7-bit: <= 9,711 (2% below 9,910) and <= 13,437 (5% above 12,798). A qualifying result still needs an independently verified guide package and passing BITS checks. Readable arms have no live joint80 slot; the empty-slot rule (whole cohort, fewer total presses than the cheapest existing profile on the cohort: 6,413 x 9 = 57,717) is reported, not relaxed.',
    'out_of_scope': ['six-bit slots (separate experiment, literals/sixbit-v1)', 'other cohorts', 'BITS changes', 'human learnability or fluency claims'],
}


def main():
    out = ROOT / 'contract.json'
    if out.exists():
        raise SystemExit('refusing to overwrite contract.json')
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
    contract = dict(CONTRACT, frozen_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'), parent_commit=head,
                    inputs={rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in INPUTS})
    out.write_text(json.dumps(contract, indent=2) + '\n')
    print(f"pinned {len(INPUTS)} inputs at {contract['frozen_at']} on parent {head[:9]}")


if __name__ == '__main__':
    main()
