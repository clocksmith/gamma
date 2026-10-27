from collections import Counter


def solve(responses):
    counts = Counter()
    for day in responses:
        counts.update(set(day))
    return min(counts, key=lambda word: (-counts[word], word))
