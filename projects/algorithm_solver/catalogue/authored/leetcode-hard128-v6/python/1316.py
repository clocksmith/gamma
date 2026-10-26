"""1316. Distinct Echo Substrings.

Exact suffix ranks and LCP range minima; O(n^2 + n log^2 n) time, O(n log n) space. No probabilistic hashes.
"""

def solve(text: str) -> int:
    n = len(text)
    suffixes = list(range(n))
    rank = [ord(char) for char in text]
    width = 1
    while width < n:
        suffixes.sort(key=lambda i: (rank[i], rank[i + width] if i + width < n else -1))
        next_rank = [0] * n
        for index in range(1, n):
            first, second = suffixes[index - 1], suffixes[index]
            a = (rank[first], rank[first + width] if first + width < n else -1)
            b = (rank[second], rank[second + width] if second + width < n else -1)
            next_rank[second] = next_rank[first] + (a != b)
        rank = next_rank
        width *= 2
    if n < 2:
        return 0
    lcp = [0] * n
    length = 0
    for start in range(n):
        order = rank[start]
        if order == 0:
            length = 0
            continue
        previous = suffixes[order - 1]
        while start + length < n and previous + length < n and text[start + length] == text[previous + length]:
            length += 1
        lcp[order] = length
        length = max(0, length - 1)
    table = [lcp]
    span = 2
    while span <= n:
        half = span // 2
        old = table[-1]
        table.append([min(old[i], old[i + half]) for i in range(n - span + 1)])
        span *= 2
    logs = [0] * (n + 1)
    for index in range(2, n + 1):
        logs[index] = logs[index // 2] + 1

    def common(a, b):
        if a == b:
            return n - a
        left, right = sorted((rank[a], rank[b]))
        left += 1
        level = logs[right - left + 1]
        return min(table[level][left], table[level][right - (1 << level) + 1])

    answer = 0
    for half in range(1, n // 2 + 1):
        previous = -1
        for start in suffixes:
            if start + 2 * half <= n and common(start, start + half) >= half:
                if previous == -1 or common(previous, start) < 2 * half:
                    answer += 1
                previous = start
    return answer


class Solution:
    def distinctEchoSubstrings(self, text: str) -> int:
        return solve(text)
