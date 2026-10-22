"""Write contract.json once, before any sixbit-v1 job runs."""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ['model.py', 'run.py', 'verify.py', 'escape6.py', 'escape6_decoder.py', 'ESCAPE6.md', 'test_sixbit.py', 'FREEZE.md',
          '../matched80-v1/run.py', '../matched80-v1/contract.json', '../matched80-v1/labels/ids.json',
          '../scale-v2/generated/manifest.json', '../scale-v2/qualification/report.json',
          '../scale-v2/qualification-rerun-v1/report.json', '../pass2/working/bitpack.py',
          '../readable-v1/literal_codec.py', '../literals.py']
CONTRACT = {
    'schema': 'gamma.sixbit.contract.v1',
    'goals': 'v2:2a/2b representation, Track A development optimization; six-bit capacity requested by the owner on 2026-10-22',
    'population': 'The 80 matched80 problems (matched80-v1 labels/ids.json), sources and both qualification receipts verified on load by matched80-v1 load_inputs(). Compact sources for A, B and C; canonical sources for A only.',
    'rules': {
        'W': 'Existing witnessed-literal rules without the mandatory 96-entry fallback (96 > 64): any single character; multi-character strings occurring in at least two distinct problems, at most 160 UTF-8 bytes, never a whole program.',
        'U': 'Unrestricted: any substring of a cohort program that is not a whole cohort program; no witness or length rule.',
        'W-strict (analytic only)': 'W with single characters also needing two witnessing problems. Not run: any entry containing a character found in one problem occurs only there.',
    },
    'experiments': {
        'A': 'Exact coverage: minimum entries such that all programs are concatenations of entries. Six-bit exact coverage is feasible iff the minimum is at most 64.',
        'B': 'Maximum coverage with at most 64 entries (phase 1), then fewest total selections among vocabularies reaching that coverage (phase 2). Presses = 7 per selection.',
        'C': 'literal-escape6-v1 (ESCAPE6.md): at most 63 entries plus ESC; minimize total presses over all 80 programs (7 per selection, 15 per escaped character).',
    },
    'jobs': {'a-u-compact': 'A/U', 'a-w-compact': 'A/W', 'b-u-compact': 'B/U', 'b-w-compact': 'B/W', 'c-w-compact': 'C/W',
             'c-u-compact': 'C/U', 'a-u-canonical': 'A/U', 'a-w-canonical': 'A/W'},
    'method': 'Exact segmentation-graph integer programs over every eligible substring (model.py); strings occurring once are private arcs. LP relaxations give node potentials; verify.py recomputes a Lagrangian bound from them over all eligible substrings, independent of the solver. Solutions are reparsed by an exact dynamic program and encoded (canonical LTD1/LTV1 at width 6 for A and B; literal-escape6-v1 for C).',
    'solver': 'scipy 1.18.0 milp and linprog (HiGHS), default options (HiGHS random_seed 0), one thread per job.',
    'limits': {'lp_seconds': 1800, 'milp_seconds': 3600, 'second_seconds': 1800, 'workers': 4},
    'limits_note': 'Host Mars (macOS, 8 cores, 24 GB). A job that reaches a time limit reports its best solution, its solver bound and gap, and is flagged machine-dependent.',
    'random_seeds': 'None.',
    'scoring': {
        'A': 'Verdict feasible / infeasible / unresolved: infeasible needs a verified bound above 64; feasible needs an independently decoded 64-entry witness.',
        'B': 'Coverage, then selections, then package bytes (dictionary plus packets); coverage upper bound from the verified certificate.',
        'C': 'Total presses, then package bytes including decoder bytes; also without decoder bytes for comparison with live profiles.',
    },
    'comparison': {'live_7_bit': 'bits-literal-joint80-7-v2: 9,910 selections x 8 presses = 79,280; package 12,798 bytes',
                   'live_8_bit': 'bits-literal-joint80-8-v1: 6,413 selections x 9 presses = 57,717; package 11,781 bytes'},
    'promotion': 'BITS_PROMOTION.md first-profile rule for an empty six-bit slot: the profile must cover its whole declared cohort and use fewer total presses than the cheapest existing profile on it (57,717). A partial-cohort B result would need its own declared cohort and the same press comparison on that cohort.',
    'predictions': [
        'P1: W-strict cannot cover problems 709, 917 and 929 (analytic).',
        'P2: Under W the minimum exceeds 64 entries; six-bit exact coverage is impossible.',
        'P3: Under U the minimum exceeds 64 entries.',
        'P4: With 64 entries, coverage is below 80 under both rules, and W covers no more than U.',
        'P5: literal-escape6-v1 covers 80/80 but needs more than 57,717 presses, so it is not promoted.',
    ],
    'pre_freeze_probes': 'During design, restricted exact-coverage ILPs on compact sources under rule U with pieces capped at 4, 8 and 16 characters reached minima of 89, 86 and 84 entries. Restricted models only bound the unrestricted minimum from above; they are design probes, not results.',
    'out_of_scope': ['BITS or live dictionary changes', 'changes to the canonical codec', 'macros or whole-program entries', 'protected or unseen problems', 'human learning'],
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
