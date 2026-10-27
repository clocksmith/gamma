"""3981. Count Distinct Ways to Form Target from Two Strings
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-distinct-ways-to-form-target-from-two-strings/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3981.Count%20Distinct%20Ways%20to%20Form%20Target%20from%20Two%20Strings/README_EN.md
Complexity: O(|target|*|word1|*|word2|) time, O(|word1|*|word2|) space.
State records last selected index independently in each word; 0 means unused. Final states exclude both unused boundaries. No skip-path overcounting; inputs preserved. Native method unconfirmed.
"""

from __future__ import annotations

def solve(word1, word2, target):
    mod = 1_000_000_007
    m, n = len(word1), len(word2)
    ways = [[0] * (n + 1) for _ in range(m + 1)]
    ways[0][0] = 1
    for ch in target:
        following = [[0] * (n + 1) for _ in range(m + 1)]
        for j in range(n + 1):
            prefix = 0
            for i in range(1, m + 1):
                prefix = (prefix + ways[i - 1][j]) % mod
                if word1[i - 1] == ch:
                    following[i][j] = prefix
        for i in range(m + 1):
            prefix = 0
            for j in range(1, n + 1):
                prefix = (prefix + ways[i][j - 1]) % mod
                if word2[j - 1] == ch:
                    following[i][j] = (following[i][j] + prefix) % mod
        ways = following
    return sum(sum(row[1:]) for row in ways[1:]) % mod
