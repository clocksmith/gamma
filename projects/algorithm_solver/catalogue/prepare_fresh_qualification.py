"""Freeze independently authored in-domain cases and exact permitted imports."""
import argparse
import ast
import html
import json
from pathlib import Path
import re
import subprocess

from . import imported_qualification as q
from . import qualification_fresh_cases as oracle
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot


class JSONNames(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in {'true', 'false', 'null'}:
            raise ValueError('unexpected bare example token')
        return ast.copy_location(ast.Constant({'true': True, 'false': False, 'null': None}[node.id]), node)


def examples(pid, raw):
    text = re.sub(r'</?(?:p|pre|div|li|ul|ol|br)\b[^>]*>', '\n', raw.decode())
    text = html.unescape(re.sub('<[^>]*>', '', text))
    result = []
    for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|$)', text, re.S):
        node = ast.parse('f(' + match[1].strip() + ')', mode='eval').body
        if not isinstance(node, ast.Call) or node.args or not node.keywords or any(k.arg is None for k in node.keywords):
            raise ValueError('unsupported public argument syntax')
        args = [ast.literal_eval(JSONNames().visit(k.value)) for k in node.keywords]
        want = ast.literal_eval(JSONNames().visit(ast.parse(match[2].strip(), mode='eval')).body)
        got = oracle.expected(pid, args)
        same = sorted(got) == sorted(want) if pid in (301, 3692) else q.exact(got, want)
        if not same:
            raise ValueError(f'fresh oracle disagrees with public example for {pid}')
        result.append({'args': args, 'expected': got, 'compare': 'return'})
    if not result:
        raise ValueError('no independently checked public examples')
    return result


def prepare(args):
    KnownSpecService.from_config(args.config, args.config_sha256)
    config = q.decode(q.read(args.config))
    gate = q.decode(q.read(config['source_access']['boundary_gate']['path']))
    boundary = _boundary_snapshot(gate)
    snapshots = {r['problem_id']: r for r in q.decode(q.read(args.statements)) if r['status'] == 'fetched'}
    # Generate before opening any candidate source.
    cases = oracle.build()
    example_counts = {}
    for pid in oracle.IDS:
        identity = f'leetcode:{pid}'
        if identity not in boundary.authorized:
            raise PermissionError('fresh target outside original permitted boundary')
        snapshot = snapshots[identity]
        authorize_before_open(identity, gate['artifact_paths'], gate['trusted_hashes'], language='python', payload_kind='statement')
        raw = q.read(snapshot['path'])
        if q.sha(raw) != snapshot['sha256']:
            raise ValueError('statement snapshot drift')
        reviewed = examples(pid, raw)
        example_counts[str(pid)] = len(reviewed)
        cases[pid].extend(reviewed)
        for case in cases[pid]:
            oracle.validate(pid, case['args'])
    sources = {}
    names = subprocess.check_output(['git', 'ls-files', 'projects/algorithm_solver/catalogue/authored'], cwd=q.REPO, text=True).splitlines()
    for name in names:
        p = Path(name)
        if len(p.parts) != 7 or p.parts[-2] not in ('python', 'javascript') or not p.stem.isdecimal() or int(p.stem) not in oracle.IDS:
            continue
        key = (int(p.stem), p.parts[-2])
        if key in sources:
            raise ValueError('ambiguous fresh source variant')
        sources[key] = q.REPO / p
    if set(sources) != {(pid, lang) for pid in oracle.IDS for lang in ('python', 'javascript')}:
        raise ValueError('fresh dual-language source denominator incomplete')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'sources').mkdir(); (args.output / 'tests').mkdir()
    jobs = []
    for (pid, language), path in sorted(sources.items()):
        identity = f'leetcode:{pid}'
        authorize_before_open(identity, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        raw = q.read(path, 1024 * 1024)
        if language == 'python':
            module = ast.parse(raw)
            entries = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'solve']
            if len(entries) != 1 or entries[0].args.vararg or entries[0].args.kwarg or entries[0].args.kwonlyargs:
                raise ValueError('explicit ordered solve signature required')
            arity = len(entries[0].args.posonlyargs) + len(entries[0].args.args)
            if any(len(case['args']) != arity for case in cases[pid]):
                raise ValueError('source/public interface arity differs')
        suffix = 'py' if language == 'python' else 'js'
        source = f'sources/{pid}.{suffix}'; tests = f'tests/{pid}.json'
        (args.output / source).write_bytes(raw)
        q.write(args.output / tests, cases[pid])
        jobs.append({'id': pid, 'language': language, 'source': source, 'source_sha256': q.sha(raw),
                     'original_source': str(path), 'tests': tests, 'tests_raw_sha256': q.file_hash(args.output / tests),
                     'tests_canonical_sha256': q.canonical_tests_hash(cases[pid]), 'case_count': len(cases[pid]),
                     'statement': snapshots[identity], 'domain_validator': 'fresh67-v1',
                     'comparison_policy': 'set-of-strings' if pid == 301 else 'permutation-of-chars' if pid == 3692 else 'exact'})
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'jobs': jobs, 'pending': [],
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'runtime': q.runtime(), 'code': q.code_pins(), 'limits': q.LIMITS,
                'additional_code': {str(Path(oracle.__file__).resolve()): q.file_hash(oracle.__file__),
                                    str(Path(__file__).resolve()): q.file_hash(__file__)},
                'max_packet_bytes': q.MAX_PACKET, 'public_examples_checked': example_counts,
                'test_authority': 'Fresh definition-level oracles authored from pinned statements before reading candidates; all public examples cross-checked; explicit domain validator runs before execution.',
                'effects': 'read-only arguments; no mutable return-to-input aliases',
                'comparison': 'exact typed returns; only 301 and 3692 permit statement-defined output permutations',
                'scope': 'Finite independent in-domain typed/local-effect checks; no universal correctness or full-domain performance proof.',
                'automatic_promotion': False, 'protected_access': False}
    q.write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'checks': sum(j['case_count'] for j in jobs), 'public_examples': sum(example_counts.values()),
            'contract_sha256': q.file_hash(args.output / 'contract.json')}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'statements', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--config-sha256', required=True)
    print(json.dumps(prepare(p.parse_args())))
