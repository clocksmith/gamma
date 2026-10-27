"""3999. Minimum Number of String Groups Through Transformations
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-number-of-string-groups-through-transformations/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3999.Minimum%20Number%20of%20String%20Groups%20Through%20Transformations/README_EN.md
Complexity: O(total characters) expected time and space.
Independent cyclic rotations, not arbitrary permutations. Booth canonicalizes each parity subsequence exactly; pair keys preserve length and order without hash-only equality. Native method unconfirmed.
"""

from __future__ import annotations

def solve(words):
    def rotation(s):
        n = len(s)
        if n <= 1:
            return s
        doubled = s + s
        a, b, offset = 0, 1, 0
        while a < n and b < n and offset < n:
            x, y = doubled[a + offset], doubled[b + offset]
            if x == y:
                offset += 1
                continue
            if x > y:
                a += offset + 1
                if a == b:
                    a += 1
            else:
                b += offset + 1
                if b == a:
                    b += 1
            offset = 0
        start = min(a, b)
        return doubled[start:start + n]
    return len({(rotation(word[::2]), rotation(word[1::2])) for word in words})
