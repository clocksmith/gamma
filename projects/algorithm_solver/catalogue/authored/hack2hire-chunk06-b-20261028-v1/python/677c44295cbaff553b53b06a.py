"""Hack2Hire 677c44295cbaff553b53b06a (Keyboard Jump Challenge) over an INFERRED spec; qualification unknown."""

def solve(keyboard, maxDistance, word):
    m, n = len(keyboard), len(keyboard[0])
    cells = {}
    for r in range(m):
        for c in range(n):
            cells.setdefault(keyboard[r][c], []).append(r * n + c)
    if any(ch not in cells for ch in word):
        return False
    big = m + n + 1
    current = frozenset(cells[word[0]])
    memo = {}
    for ch in word[1:]:
        key = (current, ch)
        if key not in memo:
            dist = [big] * (m * n)
            for cell in current:
                dist[cell] = 0
            for r in range(m):          # forward sweep of the L1 distance transform
                for c in range(n):
                    i = r * n + c
                    if r and dist[i - n] + 1 < dist[i]:
                        dist[i] = dist[i - n] + 1
                    if c and dist[i - 1] + 1 < dist[i]:
                        dist[i] = dist[i - 1] + 1
            for r in range(m - 1, -1, -1):  # backward sweep
                for c in range(n - 1, -1, -1):
                    i = r * n + c
                    if r + 1 < m and dist[i + n] + 1 < dist[i]:
                        dist[i] = dist[i + n] + 1
                    if c + 1 < n and dist[i + 1] + 1 < dist[i]:
                        dist[i] = dist[i + 1] + 1
            memo[key] = frozenset(cell for cell in cells[ch] if dist[cell] <= maxDistance)
        current = memo[key]
        if not current:
            return False
    return True


class Solution:
    def canTypeWord(self, keyboard, maxDistance, word):
        return solve(keyboard, maxDistance, word)
