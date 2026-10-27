"""411. Minimum Unique Word Abbreviation."""

def solve(target: str, dictionary: list[str]) -> str:
    """Branch on unhit difference masks; O(2^m * (m+d)) worst-case time, inputs preserved."""
    length = len(target)
    differences = set()
    for word in dictionary:
        if len(word) != length:
            continue
        difference = sum(1 << index for index, (left, right) in enumerate(zip(target, word)) if left != right)
        if difference == 0:
            return ''
        differences.add(difference)
    if not differences:
        return str(length)
    differences = sorted(differences, key=int.bit_count)
    best_mask, best_length = (1 << length) - 1, length
    visited = set()

    def token_count(mask):
        count, skipped = 0, False
        for index in range(length):
            if mask & (1 << index):
                count += 1 + skipped
                skipped = False
            else:
                skipped = True
        return count + skipped

    def search(mask):
        nonlocal best_mask, best_length
        if mask in visited:
            return
        visited.add(mask)
        size = token_count(mask)
        if size >= best_length:
            return
        uncovered = next((difference for difference in differences if not difference & mask), 0)
        if uncovered == 0:
            best_mask, best_length = mask, size
            return
        while uncovered:
            bit = uncovered & -uncovered
            uncovered -= bit
            search(mask | bit)

    search(0)
    parts, skipped = [], 0
    for index, char in enumerate(target):
        if best_mask & (1 << index):
            if skipped:
                parts.append(str(skipped))
                skipped = 0
            parts.append(char)
        else:
            skipped += 1
    if skipped:
        parts.append(str(skipped))
    return ''.join(parts)


class Solution:
    def minAbbreviation(self, target, dictionary):
        return solve(target, dictionary)
