"""Finite pool extraction from supplied, independently verified item35 state."""
from collections import Counter, defaultdict
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('fraction_repair_binned_index', Path(__file__).resolve().parents[1] / 'length-sensitive-fraction-v1/implicit.py')
implicit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(implicit)


def build(index, q, seed, denominator=1_000_000, capacity=256, pool_cap=2048):
    """No I/O. All strings/results remain private; callers export metadata only."""
    assert len(seed) == len(set(seed)) <= capacity and all(seed)
    assert type(pool_cap) is int and pool_cap >= 0
    cert = index.certificate(q, capacity, denominator)
    assert implicit.verify(index, q, capacity, denominator) == cert['numerator']
    texts = index.texts; banned = index.base.banned
    assert not set(seed) & set(banned), 'banned seed entry'
    assert all(any(word in text for text in texts.values()) for word in seed), 'nonoccurring seed entry'
    short = index.selected_vocabulary(cert['selected_pieces'], longest_first=False)
    long = index.selected_vocabulary(cert['selected_pieces'], longest_first=True)
    protected = set(seed) | set(short) | set(long)
    assert len(protected) <= pool_cap, 'protected pool tier exceeds cap'
    assert not protected & set(banned)
    uses = Counter(); owners = defaultdict(set)
    for pid, text in sorted(texts.items()):
        markers = cert['path_starts'][pid]
        starts = [i for i, row in enumerate(markers) if any(row)]
        assert starts and starts[0] == 0
        numerator = 0
        for start, end in zip(starts, starts[1:] + [len(text)]):
            row = markers[start]; assert sum(row) == 1 and all(x in (0, 1) for x in row)
            b = row.index(1); assert implicit.bin_index(end - start) == b
            word = text[start:end]; assert word and word not in banned
            uses[word] += 1; owners[word].add(pid)
            numerator += q[pid][start][b] + (9 if len(word) == 1 else -1) * denominator
        assert numerator == cert['path_numerators'][pid]
    def priority(word):
        saving = 9 * len(word) + 1 if len(word) > 1 else 0
        return (-uses[word] * saving, -len(owners[word]), len(word), word)
    proposed = sorted(set(uses) - protected, key=priority)
    admitted = proposed[:pool_cap - len(protected)]
    candidates = sorted(protected | set(admitted))
    provenance = {word: [label for label, words in [('seed', set(seed)), ('top_short', set(short)),
                                                   ('top_long', set(long)), ('relaxed_path', set(uses))]
                         if word in words] for word in candidates}
    return candidates, {'seed_entries': len(seed), 'protected_entries': len(protected),
                        'top_short_entries': len(short), 'top_long_entries': len(long),
                        'path_entries_proposed': len(proposed), 'path_entries_admitted': len(admitted),
                        'path_entries_omitted': len(proposed) - len(admitted),
                        'pool_entries': len(candidates), 'provenance': provenance,
                        'parent_numerator': cert['numerator'], 'parent_denominator': denominator}
