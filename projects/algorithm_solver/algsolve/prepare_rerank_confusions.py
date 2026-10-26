"""Prepare a source-bound, development-only contract discrimination diagnostic.

Uses already authorized statement snapshots, not solutions or test payloads.
Independent review must approve query labels before the model run. All inputs
are development material; this is neither fresh confirmation nor training.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re

from .rerank_policy_comparison import digest, validate_cohort

FREEZES = {
    'admitted-freeze-v2': 'fd0baa979cc3a40801ca3a69e4704c382a6dda525a9d6398a2d19ef89780684c',
    'fresh-freeze-v3': '96fd1d99ddb771405989764ad4f6b0249b116205771c9fe29df68cc2ff446679',
    'expanded-diagnostic-freeze-v1': '38aa4b0b1e6e205c47342da786c9dc25ff9f6c10a77511ae831ed0a99c3bcdd5',
}
GROUPS = {
    'sentence': [68, 1451, 1859],
    'linked_list': [2074, 2807, 1721, 876],
    'integer_construction': [2177, 2178, 2028, 1362],
    'contiguous': [1839, 1456, 1524, 2444, 2419],
}
# Query wording is authored for this diagnostic, never sampled from confirmations.
QUERIES = [
    ('sentence', 68, 'positive', 'Wrap these words into lines of a supplied width, greedily fitting as many words as possible. Every line must have that width. Spread padding evenly across gaps, with leftover spaces toward the left; use single gaps and right padding on the final line.'),
    ('sentence', 1451, 'positive', 'Rearrange a sentence from shortest word to longest. Words of equal length must keep their original order. Use single spaces, capitalize the new first letter, and lowercase the other words.'),
    ('sentence', 1859, 'positive', 'The words in this sentence have been shuffled. Each ends in a digit from 1 to 9 giving its original position. Restore the sentence in that order and remove the position digits.'),
    ('sentence', None, 'ambiguous', 'Rearrange the words in this sentence into the right order.'),
    ('sentence', None, 'mismatch', 'Sort the words of a sentence alphabetically, preserving each word\'s capitalization, and return them joined by one space.'),
    ('linked_list', 2074, 'positive', 'Divide a linked list from the front into groups of requested sizes 1, 2, 3, and so on. Reverse only groups whose actual size is even, including a short final group if its actual size is even. Return the modified head.'),
    ('linked_list', 2807, 'positive', 'For every neighboring pair in an integer linked list, insert a new node containing their greatest common divisor. Keep the original nodes in their order and return the resulting head.'),
    ('linked_list', 1721, 'positive', 'In a singly linked list, exchange the values stored at the kth node from the front and the kth from the back. Count positions starting at one and return the head.'),
    ('linked_list', 876, 'positive', 'Return the node in the middle of this singly linked list. If its length is even, choose the later of the two middle nodes.'),
    ('linked_list', None, 'ambiguous', 'I need the middle node of a linked list; the list can have even length, and I have not decided which middle to use.'),
    ('linked_list', None, 'mismatch', 'Return the middle node of a singly linked list, choosing the earlier middle when there are two.'),
    ('integer_construction', 2177, 'positive', 'Find three consecutive integers whose sum is the given integer. Return them in increasing order, or an empty array if this is impossible.'),
    ('integer_construction', 2178, 'positive', 'Express this integer as a sum of as many distinct positive even integers as possible. Return any maximizing set in any order, or an empty list when no such split exists.'),
    ('integer_construction', 2028, 'positive', 'Some outcomes of six-sided dice are missing. Given the observed rolls, the total average, and the number missing, return any possible missing outcomes from 1 through 6 attaining that average, or an empty array if impossible.'),
    ('integer_construction', 1362, 'positive', 'Given num, choose two positive integers with the smallest absolute difference, requiring their product to be either num plus one or num plus two. Return the pair in either order.'),
    ('integer_construction', None, 'ambiguous', 'Split this integer into a collection of numbers. I have not specified how many, whether repetition is allowed, or which collection to prefer.'),
    ('integer_construction', None, 'mismatch', 'Split this positive integer into the maximum possible number of positive even summands; repeated summands are allowed. Return an empty list if impossible.'),
    ('contiguous', 1839, 'positive', 'In a string containing only vowels, find the longest contiguous stretch containing all five vowels at least once, in nondecreasing alphabetical order. Return its length, or zero if none exists.'),
    ('contiguous', 1456, 'positive', 'Given a lowercase string and k, return the largest count of vowels in any contiguous window of exactly k characters.'),
    ('contiguous', 1524, 'positive', 'Count the contiguous subarrays of an integer array whose sum is odd. Return the count modulo 1000000007.'),
    ('contiguous', 2444, 'positive', 'Count contiguous subarrays whose minimum equals minK and whose maximum equals maxK. Both bounds must actually occur inside each counted subarray.'),
    ('contiguous', 2419, 'positive', 'Find the greatest bitwise AND achievable by a nonempty contiguous subarray of this integer array. Among subarrays achieving it, return the greatest length.'),
    ('contiguous', None, 'ambiguous', 'Find the best contiguous part of this sequence. I have not specified whether best refers to its length, sum, or contents.'),
    ('contiguous', None, 'mismatch', 'Count all contiguous subarrays whose minimum is at least minK and maximum is at most maxK; neither bound needs to occur.'),
]


def read_pinned(path, expected, limit):
    path = Path(path)
    if path.stat().st_size > limit:
        raise ValueError('artifact exceeds bound: ' + str(path))
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('artifact identity changed: ' + str(path))
    return raw


def description(raw):
    markup = raw.decode('utf-8')
    # A numeric superscript is mathematical content, not a word separator.
    markup = re.sub(r'<sup\b[^>]*>\s*([+-]?\d+)\s*</sup>', r'^\1', markup)
    text = html.unescape(re.sub('<[^>]*>', ' ', markup))
    text = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'\bExample\s+1\s*:', text, maxsplit=1)
    if len(parts) != 2 or not parts[0].strip():
        raise ValueError('statement requires a description followed by Example 1')
    return parts[0].strip()


def prepare(root, gate_path, gate_sha256):
    from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
    root = Path(root)
    gate = json.loads(read_pinned(gate_path, gate_sha256, 1024**2))
    ids = {i for group in GROUPS.values() for i in group}
    pins = {}
    for name, expected in FREEZES.items():
        freeze = json.loads(read_pinned(root/name/'contract.json', expected, 16*1024**2))
        for job in freeze['jobs']:
            if job['id'] not in ids:
                continue
            pin = job['statement']
            if job['id'] in pins and pins[job['id']] != pin:
                raise ValueError('inconsistent statement authority')
            pins[job['id']] = pin
    if set(pins) != ids:
        raise ValueError('missing statement identities')
    documents = {}
    for pid, pin in sorted(pins.items()):
        authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'],
                              language='python', payload_kind='statement')
        raw = read_pinned(pin['path'], pin['sha256'], 1024**2)
        documents[pid] = {'key': f'leetcode:{pid}', 'text': description(raw)}
    cases = []
    for index, (group, target, kind, query) in enumerate(QUERIES):
        members = GROUPS[group]
        offset = index % len(members)
        members = members[offset:] + members[:offset]
        cases.append({'id': f'{group}-{index+1:02d}', 'group': group, 'kind': kind,
                      'query': query, 'target': f'leetcode:{target}' if target is not None else None,
                      'documents': [documents[pid] for pid in members]})
    cohort = {'schema': 'gamma.rerank-policy-input.v1', 'partition': 'development',
              'scope': 'Authored development queries over 16 authorized statements in supplied confusion groups. '
                       'Not catalogue retrieval, held-out confirmation, or training data approval.',
              'cases': cases}
    validate_cohort(cohort)
    provenance = {'schema': 'gamma.rerank-confusion-provenance.v1',
                  'cohort_sha256': digest(cohort), 'gate_sha256': gate_sha256,
                  'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'statement_pins': {str(pid): pin for pid, pin in sorted(pins.items())},
                  'freeze_sha256': FREEZES, 'queries': len(cases), 'documents': len(documents),
                  'source_reads': 0, 'test_payload_reads': 0, 'confirmation_reads': 0,
                  'independent_review_required': True, 'recognition_qualified': False}
    return cohort, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualification-root', type=Path, required=True)
    parser.add_argument('--gate', type=Path, required=True)
    parser.add_argument('--gate-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cohort, provenance = prepare(args.qualification_root, args.gate, args.gate_sha256)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in [('cohort.json', cohort), ('provenance.json', provenance)]:
        (args.output/name).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'queries': len(cohort['cases']), 'cohort_sha256': digest(cohort),
                      'independent_review_required': True}))


if __name__ == '__main__':
    main()
