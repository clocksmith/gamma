"""1531. String Compression II: memoized suffix/deletion DP over retained runs; O(n^2*(k+1)) time and O(n*(k+1)) space."""

from functools import lru_cache


def solve(s: str, k: int) -> int:
    @lru_cache(None)
    def best(start: int, remaining: int) -> int:
        if remaining < 0:
            return len(s) + 1
        if len(s) - start <= remaining:
            return 0
        answer = best(start + 1, remaining - 1)
        kept = removed = 0
        for end in range(start, len(s)):
            if s[end] == s[start]:
                kept += 1
            else:
                removed += 1
            if removed > remaining:
                break
            encoded = 1 if kept == 1 else 1 + len(str(kept))
            answer = min(answer, encoded + best(end + 1, remaining - removed))
        return answer

    return best(0, k)


class Solution:
    def getLengthOfOptimalCompression(self, s: str, k: int) -> int:
        return solve(s, k)
