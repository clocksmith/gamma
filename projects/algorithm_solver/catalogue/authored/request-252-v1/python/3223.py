from collections import Counter


def solve(s):
    """Remove pairs of each letter until one or two occurrences remain."""
    return sum(1 if count % 2 else 2 for count in Counter(s).values())
