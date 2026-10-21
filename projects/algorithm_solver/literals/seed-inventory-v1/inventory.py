"""Deterministic physical-line witnesses, not semantic or AST equivalence."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def build(manifests):
    groups = {}
    sources = []
    inputs = []
    identities = set()
    labels = set()
    source_paths = set()
    for manifest in sorted(map(Path, manifests), key=lambda p: p.parent.name):
        label = manifest.parent.name
        if label in labels:
            raise ValueError('Duplicate input label')
        labels.add(label)
        raw = manifest.read_bytes()
        document = json.loads(raw)
        inputs.append({'label': label, 'manifest_sha256': digest(raw)})
        rows = document['source_inventory']
        if not rows:
            raise ValueError('Empty source inventory')
        for row in sorted(rows, key=lambda r: (r['language'], int(r['id']), r['path'])):
            language = row['language']
            raw_id = row['id']
            if type(raw_id) is not int:
                raise ValueError('Problem ID must be an integer, not bool or coerced text')
            problem_id = raw_id
            if language not in ('javascript', 'python') or problem_id <= 0:
                raise ValueError('Unsupported identity')
            relative = Path(row['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe source path')
            root = manifest.parent.resolve()
            path = root / relative
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Source escapes input root')
            if relative.suffix != {'javascript': '.js', 'python': '.py'}[language]:
                raise ValueError('Language extension mismatch')
            if not relative.stem.isascii() or not relative.stem.isdecimal() or int(relative.stem) != problem_id:
                raise ValueError('Numeric source filename must match problem ID')
            if path.resolve() in source_paths:
                raise ValueError('Duplicate resolved source path')
            source_paths.add(path.resolve())
            identity = (language, problem_id)
            if identity in identities:
                raise ValueError('Duplicate language/problem identity')
            identities.add(identity)
            data = path.read_bytes()
            if digest(data) != row['sha256']:
                raise ValueError('Source digest mismatch: ' + str(relative))
            source_id = label + '/' + relative.as_posix()
            sources.append({'source': source_id, 'language': language,
                            'problem_id': problem_id, 'sha256': digest(data)})
            # Normalize line terminators only. Preserve ALL horizontal whitespace.
            text = data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
            for number, literal in enumerate(text.split('\n'), 1):
                if not literal.strip():
                    continue
                groups.setdefault((language, literal), []).append({
                    'source': source_id, 'problem_id': problem_id, 'line': number})
    witnesses = []
    for (language, literal), occurrences in sorted(groups.items()):
        ids = sorted({entry['problem_id'] for entry in occurrences})
        if len(ids) < 2:
            continue
        witnesses.append({'language': language, 'literal': literal,
                          'literal_sha256': digest(literal.encode('utf-8')),
                          'distinct_problem_ids': ids, 'distinct_problem_count': len(ids),
                          'occurrence_count': len(occurrences),
                          'occurrences': sorted(occurrences, key=lambda x: (x['source'], x['line']))})
    return {'schema': 'gamma.literal-line-witnesses.v1',
            'policy': 'UTF-8; CRLF/CR/LF terminators normalized and excluded; all indentation and trailing whitespace preserved; blank lines excluded. Complete physical lines, NOT necessarily complete statements. No AST, alpha-renaming or semantic equivalence claim.',
            'inputs': inputs, 'sources': sources, 'source_count': len(sources),
            'distinct_problem_count': len({r['problem_id'] for r in sources}),
            'witness_count': len(witnesses), 'witnesses': witnesses}


def render(document):
    return json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifests', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = render(build(args.manifests))
    args.output.write_text(output, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
