"""Write contract.json for roles-v1 (refuses to overwrite)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sha = lambda b: hashlib.sha256(b).hexdigest()
W = Path('/home/x/Documents/Codex/2026-10-19/task/literal-admission500-v1')
ACORN = Path('/usr/share/nodejs/acorn')


def tree_sha(root):
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob('*') if p.is_file()):
        h.update(str(f.relative_to(root)).encode() + b'\0' + hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def main():
    out = HERE / 'contract.json'; assert not out.exists()
    mc = json.loads((LIT / 'minify-control-v1/contract.json').read_text())
    audit = W / 'roles/audit.json'
    code = ['roles-v1/FREEZE.md', 'roles-v1/HUMAN_STUDY.md', 'roles-v1/roles.mjs', 'roles-v1/binding.py', 'roles-v1/decoder.mjs',
            'roles-v1/measure.py', 'roles-v1/evidence.py', 'roles-v1/test_roles.py', 'roles-v1/make_contract.py',
            'style150-v1/style.py', 'admission500-v1/stage.py', 'admission500-v1/harness.cjs', 'admission500-v1/harness-exact-integer.cjs',
            'admission500-v1/qualify_rules.py', 'verify_execution.py', '../algsolve/judge/sandbox.py',
            *mc['code_hashes']]
    c = {'schema': 'gamma.roles-v1.contract.v1',
         'goal': 'Declare each identifier once per program and reference it by role (B), against the minified (L-Om) and '
                 'shared-style (L-R) literal baselines, with a rename-only attribution control (N); dev-val 100, every action counted',
         'inputs': {'minify_control_contract_sha256': sha((LIT / 'minify-control-v1/contract.json').read_bytes()),
                    'audit_sha256': sha(audit.read_bytes()), 'acorn_version': '8.16.0', 'acorn_sha256': tree_sha(ACORN)},
         'partition': {'fit': 'minify-control-v1 dev_fit (300)', 'measure': 'minify-control-v1 dev_val (100), never fitted',
                       'final_heldout': 'not opened in this stage'},
         'arms': [f'{r}-{p}-{w}' for w in (128, 256) for p in ('Om', 'R') for r in ('L', 'B', 'N')],
         'search': {**mc['search'], 'absent_slot_proposals': 16,
                    'start': 'fallback alphabet (96); B also END. Greedy refill, matched80-v3 exact local search',
                    'proposer': 'L: chosen-source spans only (minify-control-v1); B/N: absent END (B), the top 16 absent slots by '
                                'dev-fit occurrences (support >= 2 problems), then chosen-source spans over text-contiguous runs'},
         'controls': {'L-Om-128': 41394, 'L-Om-256': 27098, 'L-R-128': 14014, 'L-R-256': 8948},
         'actions': 'literal + reference + declaration + binding (END) + navigation (0) + correction (0) + submission (1) per program',
         'promotion': {'min_reduction': 0.05, 'min_improved': 60, 'max_worsened': 25,
                       'rule': 'Per width, a B arm is promoted only if, against both L-R and L-Om at that width: every dev-val program '
                               'decodes exactly and passes every frozen case (P1); total actions at least 5% lower (P2); median and p90 '
                               'actions both lower (P3); at least 60 of 100 programs improve and at most 25 worsen (P4). Among those, '
                               'fewest actions, ties by package bytes with decoder. A conditional gain is the same test against the '
                               'same-pool L arm only. Promotion permits proposing a separately frozen confirmation and the human '
                               'study; it is not M1 and not a BITS candidate.'},
         'm1_gates': mc['m1_gates'],
         'predictions': {
             'R1': 'L arms reproduce the minify-control-v1 Fdev dev-val selections exactly (41,394; 27,098; 14,014; 8,948).',
             'R2': 'At both widths B-Om uses at least 15% fewer dev-val actions than L-Om, and more than 80 of 100 programs improve.',
             'R3': 'At both widths B-R is not more than 1% below L-R in actions.',
             'R4': 'No B arm is promoted at either width.',
             'R5': 'At both widths declarations cost actions (B-Om above N-Om), and N-Om stays above L-R.',
             'R6': 'Every decoded dev-val program in every arm decodes exactly and passes every frozen case.',
             'R7': 'No arm meets the M1 indicator on dev-val (median <= 32, p95 <= 96, fallback <= 10%).'},
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
