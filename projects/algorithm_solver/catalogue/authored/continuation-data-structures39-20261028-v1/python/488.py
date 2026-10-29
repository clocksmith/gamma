"""Original frontend 488 variant; qualification unknown."""
from collections import deque


def _collapse(s: str) -> str:
    changed = True
    while changed:
        changed = False
        i = 0
        n = len(s)
        while i < n:
            j = i
            while j < n and s[j] == s[i]:
                j += 1
            if j - i >= 3:
                s = s[:i] + s[j:]
                changed = True
                break
            i = j
    return s


def solve(board: str, hand: str) -> int:
    b0 = _collapse(board)
    h0 = "".join(sorted(hand))
    q = deque([(b0, h0, 0)])
    visited = {(b0, h0)}
    while q:
        b, h, steps = q.popleft()
        if not b:
            return steps
        if not h:
            continue
        for hi, ch in enumerate(h):
            if hi > 0 and h[hi] == h[hi - 1]:
                continue
            nh = h[:hi] + h[hi + 1:]
            for bi in range(len(b) + 1):
                if bi > 0 and b[bi - 1] == ch:
                    continue
                pick = False
                if bi < len(b) and b[bi] == ch:
                    pick = True
                elif 0 < bi < len(b) and b[bi - 1] == b[bi] and b[bi] != ch:
                    pick = True
                if not pick:
                    continue
                nb = _collapse(b[:bi] + ch + b[bi:])
                if not nb:
                    return steps + 1
                state = (nb, nh)
                if state not in visited:
                    visited.add(state)
                    q.append((nb, nh, steps + 1))
    return -1


findMinStep = solve


class Solution:
    def findMinStep(self, board: str, hand: str) -> int:
        return solve(board, hand)
