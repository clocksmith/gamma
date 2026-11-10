"""Explicit development continuation: fixed ASCII literal alphabets, no escapes."""
import argparse
import json
from pathlib import Path
import time

import run
from core import pair_fit, sha


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--service', type=Path, required=True)
    p.add_argument('--service-sha256', required=True)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    if args.output.resolve().is_relative_to(run.ROOT):
        raise ValueError('Private output must stay outside Git')
    previous = json.loads((args.previous / 'results.json').read_bytes())
    split_raw = (run.LITERALS / 'cost-decomposition-v1/contract.json').read_bytes()
    if sha(split_raw) != 'a2c501792e4ef369a1f2630fd4ffd3b6623c1146ca3d7aac7115b469efe8cd61':
        raise ValueError('Partition changed')
    split = json.loads(split_raw)['partition']
    args.output.mkdir(parents=True, exist_ok=False)
    service = run.KnownSpecService.from_config(args.service.resolve(), args.service_sha256)
    contract = dict(previous['contract'])
    contract.update(service_sha256=args.service_sha256,
        controls='Fixed ASCII-98 and ASCII-128 character seeds plus flat pair merges; original six-bit table unchanged.',
        prior_development_report_sha256=sha((args.previous / 'results.json').read_bytes()),
        prior_validation_exposed=True)
    contract['code_pins'] = {str(p.relative_to(run.ROOT)): sha(p.read_bytes()) for p in
        [Path(__file__), run.HERE/'core.py', run.HERE/'run.py', run.LITERALS/'literals.py',
         run.LITERALS/'pass2/working/bitpack.py', run.LITERALS/'macro-fragment-compare-v1/shapes.py',
         run.LITERALS/'macro-fragment-compare-v1/js_shapes.cjs']}
    run.write(args.output / 'contract.json', contract)
    report = {k: v for k, v in previous.items() if k not in ['contract', 'languages', 'elapsed_seconds']}
    report.update(contract=contract, languages={})
    start = time.monotonic()
    for language in ['javascript', 'python']:
        folder = args.output / language
        folder.mkdir()
        fit, members = run.materialize(service, split['dev_fit'], language, folder / 'fit')
        old_members = previous['languages'][language]['fit_membership']
        if members != old_members:
            raise ValueError('Development source membership changed')
        metadata, errors = run.shapes.shapes(fit, language)
        if errors:
            raise ValueError('AST bans unavailable')
        banned = {s.encode().strip() for s in fit.values()}
        for pid, source in fit.items():
            raw = source.encode()
            banned.update(raw[a:b].strip() for a, b in metadata[pid]['banned'])
        old_seal = args.previous / language / 'sealed-tables.json'
        if sha(old_seal.read_bytes()) != previous['languages'][language]['seal_sha256']:
            raise ValueError('Original six-bit table changed')
        tables = {'6': json.loads(old_seal.read_bytes())['6']}
        fits = {'6': {'method': previous['languages'][language]['fit']['6']['method'],
            **run.evaluate(fit, tables['6'], 6, 300)}}
        trials = {}
        for width in [7, 8]:
            choices = []
            for name, initial in [('ascii98', [chr(n) for n in [9, 10, 13] + list(range(32, 127))]),
                                  ('ascii128', [chr(n) for n in range(128)])]:
                dictionary, trace = pair_fit(fit, initial, 1 << width, banned)
                result = run.evaluate(fit, dictionary, width, 300)
                trials[str(width) + '-' + name] = {'summary': result['summary'], 'merges': trace}
                choices.append((name, dictionary, result))
            name, dictionary, result = min(choices, key=lambda x: (-x[2]['summary']['represented'],
                (x[2]['summary']['selections'] or {'total': 0})['total'], x[2]['summary']['dictionary_bytes'], x[0]))
            tables[str(width)] = dictionary
            fits[str(width)] = {'method': name, **result}
        run.write(folder / 'sealed-tables.json', tables)
        seal = sha((folder / 'sealed-tables.json').read_bytes())
        validation, vmembers = run.materialize(service, split['dev_val'], language, folder / 'validation')
        if vmembers != previous['languages'][language]['validation_membership']:
            raise ValueError('Validation source membership changed')
        values = {w: run.evaluate(validation, d, int(w), 100, folder / ('validation-' + w)) for w, d in tables.items()}
        for w, d in tables.items():
            if run.evaluate(fit, d, int(w), 300, folder / ('fit-' + w)) != {k: v for k, v in fits[w].items() if k != 'method'}:
                raise ValueError('Fitting receipt changed')
        report['languages'][language] = {'fit_membership': members, 'validation_membership': vmembers,
            'fit': fits, 'validation': values, 'trials': trials, 'seal_sha256': seal}
        print(language, {w: r['summary'] for w, r in values.items()}, flush=True)
    report['elapsed_seconds'] = time.monotonic() - start
    run.write(args.output / 'results.json', report)
    run.write(args.report, report)


if __name__ == '__main__':
    main()
