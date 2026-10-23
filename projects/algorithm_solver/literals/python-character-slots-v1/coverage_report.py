"""Post-run coverage attribution; does not amend frozen search or verdicts."""
import argparse
import json
from pathlib import Path
import report
from common import HERE, checked, sha, write


def summarize(seed, final, texts, rows, validation_ids):
    removed = {s for s in seed if len(s) == 1} - set(final)
    ids = list(map(str, validation_ids))
    present = set(''.join(texts[pid] for pid in ids))
    exposed = {pid for pid in ids if removed & set(texts[pid])}
    failed = {pid for pid in ids if not rows[pid]['encodable']}
    return {
        'removed_character_entries': len(removed),
        'removed_characters_present_in_validation': len(removed & present),
        'validation_programs': len(ids),
        'validation_programs_exposed_to_removed_characters': len(exposed),
        'validation_coverage_failures': len(failed),
        'failed_programs_exposed_to_removed_characters': len(exposed & failed),
        'covered_programs_exposed_to_removed_characters': len(exposed - failed),
        'failed_programs_without_removed_characters': len(failed - exposed),
    }


def main(folder):
    c = json.loads((HERE/'contract.json').read_text())
    # Reuse the separate full replay, never a raw cost or coverage flag on trust.
    result = report.replay(folder, c)
    rows = []
    for arm in result['arms']:
        if arm['arm'] not in ('fixed96', 'optional'):
            continue
        width, name = arm['width'], arm['arm']
        root = folder/f'w{width}'/name
        seed = checked(c['inputs'][str(width)]['seed_dictionary'])
        final = json.loads((root/'dictionary.json').read_text())
        texts = json.loads((root/'sources.json').read_text())
        rows.append({'width': width, 'arm': name,
                     **summarize(seed, final, texts, arm['per_problem'], c['partition']['dev_val'])})
    evidence = {
        'contract_sha256': sha((HERE/'contract.json').read_bytes()),
        'private_results_sha256': sha((folder/'results.json').read_bytes()),
        'arms': rows,
        'interpretation': 'Descriptive exposure counts, not causal attribution. '
            'Removed character identities remain private. Covered exposed programs '
            'may use learned literals. Nine-program development observations only; '
            'frozen verdicts and JavaScript M1-GAP rows are unchanged.',
    }
    (HERE/'evidence').mkdir(exist_ok=True)
    write(HERE/'evidence/coverage.json', evidence)
    lines = ['# Validation coverage diagnostics', '',
             '[Metadata](evidence/coverage.json); [main report](README.md).', '',
             'Post-run descriptive reporting requested in Claude’s prelaunch review. '
             'The frozen search, qualification reuse and verdicts are unchanged.', '',
             '| Capacity | Arm | Removed characters | Removed characters seen in validation | Exposed programs | Exposed covered / failed |',
             '| ---: | --- | ---: | ---: | ---: | --- |']
    for row in rows:
        lines.append(f"| {2**row['width']} | {row['arm']} | {row['removed_character_entries']} | "
                     f"{row['removed_characters_present_in_validation']} | "
                     f"{row['validation_programs_exposed_to_removed_characters']} | "
                     f"{row['covered_programs_exposed_to_removed_characters']} / "
                     f"{row['failed_programs_exposed_to_removed_characters']} |")
    lines += ['', evidence['interpretation'], '',
              'Any cost row with fewer than nine covered validation programs describes '
              'only that covered subset. Its actions, quantiles, fraction and package '
              'cannot be compared as full-cohort totals. Every missing program remains '
              'in the frozen denominator and blocks readiness. No validation repair.', '',
              'Rebuild after the main reporter using `coverage_report.py --run <private-run>`.', '']
    (HERE/'COVERAGE.md').write_text('\n'.join(lines))
    readme = HERE/'README.md'
    link = '[Coverage diagnostics](COVERAGE.md)'
    if readme.exists() and link not in readme.read_text():
        with readme.open('a') as handle:
            handle.write('\n'+link+': incomplete coverage rows above are partial costs, '
                         'not full-cohort comparisons.\n')
    print(json.dumps(evidence, sort_keys=True))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    main(p.parse_args().run)
