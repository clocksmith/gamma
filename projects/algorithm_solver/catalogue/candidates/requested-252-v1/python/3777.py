"""3777. Minimum Deletions to Make Alternating Substring
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-deletions-to-make-alternating-substring/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3777.Minimum%20Deletions%20to%20Make%20Alternating%20Substring/README_EN.md
Complexity: O((n+q) log n) time; O(n+q) space.
Canonical solve(s,queries); native stub pending. Flips update private string state; deletion queries do not delete characters.
"""

from __future__ import annotations

def solve(s, queries):
    characters = list(s)
    n = len(s)
    tree = [0] * (n + 1)
    def add(index, change):
        while index <= n:
            tree[index] += change
            index += index & -index
    def prefix(index):
        result = 0
        while index:
            result += tree[index]
            index -= index & -index
        return result
    for right in range(1, n):
        add(right, int(characters[right - 1] == characters[right]))
    answers = []
    for query in queries:
        if query[0] == 2:
            answers.append(prefix(query[2]) - prefix(query[1]))
            continue
        position = query[1]
        for right in (position, position + 1):
            if 0 < right < n:
                add(right, -int(characters[right - 1] == characters[right]))
        characters[position] = 'B' if characters[position] == 'A' else 'A'
        for right in (position, position + 1):
            if 0 < right < n:
                add(right, int(characters[right - 1] == characters[right]))
    return answers
