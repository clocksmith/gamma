from collections import Counter


def solve(s):
    counts = Counter(s)
    half = ''.join(character * (counts[character] // 2) for character in sorted(counts))
    middle = ''.join(character for character in sorted(counts) if counts[character] % 2)
    return half + middle + half[::-1]
