"""899. Orderly Queue."""

def solve(s: str, k: int) -> str:
    """O(n) for k=1 via minimum rotation; O(n log n) sorting otherwise; O(n) space."""
    if k > 1:
        return ''.join(sorted(s))
    size = len(s)
    doubled = s + s
    first, second, offset = 0, 1, 0
    while first < size and second < size and offset < size:
        left = doubled[first + offset]
        right = doubled[second + offset]
        if left == right:
            offset += 1
            continue
        if left > right:
            first += offset + 1
            if first == second:
                first += 1
        else:
            second += offset + 1
            if first == second:
                second += 1
        offset = 0
    start = min(first, second)
    return doubled[start:start + size]


class Solution:
    def orderlyQueue(self, s: str, k: int) -> str:
        return solve(s, k)
