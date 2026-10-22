"""Extract pinned LeetCodeDataset difficulty and topic tags for the matched 80 problems.

Run on 128 from this directory with the IDs file; reads only the pinned raw files,
verifies their recorded hashes, and writes labels.json. The primary-tag precedence is
frozen here before any arm result exists; it groups results and is not a family claim.
Usage: python3 extract_labels.py <raw-data-dir> <ids.json> <labels.json>
"""
import hashlib
import json
import sys
from pathlib import Path

# Most algorithm-specific first; a problem's primary tag is its first tag in this order.
PRECEDENCE = ['Dynamic Programming', 'Memoization', 'Sliding Window', 'Prefix Sum', 'Two Pointers', 'Binary Search',
              'Divide and Conquer', 'Monotonic Stack', 'Stack', 'Queue', 'Heap (Priority Queue)', 'Trie',
              'Counting Sort', 'Counting', 'Hash Table', 'Bit Manipulation', 'Greedy', 'Sorting',
              'String Matching', 'Simulation', 'Combinatorics', 'Number Theory', 'Geometry', 'Math', 'Matrix', 'String', 'Array']


def main():
    raw, ids_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    if out.exists():
        raise SystemExit(f'refusing to overwrite {out}')
    ids = json.loads(ids_path.read_text())
    pins = [r for r in json.loads((raw / 'fetch_manifest.json').read_text())['records'] if 'LeetCodeDataset' in r['source']]
    labels, files = {}, {}
    for pin in pins:
        path = raw / pin['path'].split('data/raw/', 1)[1]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != pin['sha256']:
            raise SystemExit(f'pinned file changed: {path}')
        files[pin['file']] = {'sha256': digest, 'revision': pin['revision'], 'source': pin['source']}
        for line in path.open():
            row = json.loads(line)
            qid = int(row['question_id'])
            if qid in ids and qid not in labels:
                tags = row['tags'] or []
                unknown = [t for t in tags if t not in PRECEDENCE]
                if unknown:
                    raise SystemExit(f'tag outside the frozen precedence: {unknown}')
                labels[qid] = {'difficulty': row['difficulty'], 'tags': tags, 'task_id': row['task_id'], 'file': pin['file'],
                               'primary_tag': min(tags, key=PRECEDENCE.index) if tags else None}
    missing = [i for i in ids if i not in labels]
    if missing:
        raise SystemExit(f'unlabelled problems: {missing}')
    out.write_text(json.dumps({'schema': 'gamma.matched80.labels.v1', 'files': files, 'precedence': PRECEDENCE,
                               'extractor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               'labels': {str(k): labels[k] for k in sorted(labels)}}, indent=1) + '\n')
    print(json.dumps({'labelled': len(labels)}))


if __name__ == '__main__':
    main()
