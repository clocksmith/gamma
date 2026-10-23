"""Write contract.json for structural-v1 (refuses to overwrite)."""
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
    audit = W / 'structural/audit.json'
    code = ['structural-v1/FREEZE.md', 'structural-v1/components.json', 'structural-v1/matcher.mjs', 'structural-v1/typed.py',
            'structural-v1/decoder.mjs', 'structural-v1/measure.py', 'structural-v1/test_structural.py', 'structural-v1/make_contract.py',
            *mc['code_hashes']]
    c = {'schema': 'gamma.structural-v1.contract.v1',
         'goal': 'Typed, parameterized components (T) against literal-only dictionaries (L) on dev-val 100, pools O/Om/R',
         'inputs': {'minify_control_contract_sha256': sha((LIT / 'minify-control-v1/contract.json').read_bytes()),
                    'audit_sha256': sha(audit.read_bytes()), 'acorn_version': '8.16.0', 'acorn_sha256': tree_sha(ACORN),
                    'admissible': {p: v['admissible'] for p, v in json.loads(audit.read_text())['pools'].items()}},
         'partition': {'fit': 'minify-control-v1 dev_fit (300)', 'measure': 'minify-control-v1 dev_val (100)',
                       'final_heldout': 'not opened in this stage'},
         'search': {**mc['search'], 'proposer': 'L: chosen-source spans only; T: absent admissible components first, then spans over text-contiguous literal runs'},
         'm1_gates': mc['m1_gates'],
         'predictions': {
             'E1': 'At 256, T-R uses fewer dev-val selections than L-R, but less than 5% fewer.',
             'E2': "At 256, T's relative reduction over L is largest on R, then Om, then O.",
             'E3': 'Every L arm reproduces the dev-val selections of the matching minify-control-v1 Fdev arm exactly.',
             'E4': "In all 6 pool-width pairs, T's package bytes including the decoder exceed L's.",
             'E5': 'No arm meets M1 on dev-val (median above 32).',
             'E6': 'Every packet decodes; zero failures.',
             'E7': 'The T-R-256 final dictionary keeps components from at least 3 of the 4 families.'},
         'selection_rule': 'Per width, fewest dev-val selections, ties by package bytes with decoder; a T candidate only if it beats its pool L arm. Confirmation is a separate frozen step needing the owner.',
         'code_hashes': {rel: sha((LIT / rel).read_bytes()) for rel in dict.fromkeys(code)}}
    out.write_text(json.dumps(c, indent=1, sort_keys=True) + '\n'); print(sha(out.read_bytes()))


if __name__ == '__main__':
    main()
