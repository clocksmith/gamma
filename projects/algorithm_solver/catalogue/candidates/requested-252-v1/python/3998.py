"""3998. Transform Binary String Using Subsequence Sort
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/transform-binary-string-using-subsequence-sort/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3998.Transform%20Binary%20String%20Using%20Subsequence%20Sort/README_EN.md
Complexity: O(|s| + sum |strs[i]|) time, O(|s|) auxiliary space.
Reachability preserves total zeros and can only move zeros left. Earliest possible wildcard zeros maximize every prefix, so they provide a complete feasibility check. Native method unconfirmed.
"""

from __future__ import annotations

def solve(s, strs):
    prefix = [0]
    for ch in s:
        prefix.append(prefix[-1] + int(ch == '0'))
    total = prefix[-1]
    answer = []
    for pattern in strs:
        extra = total - pattern.count('0')
        if extra < 0 or extra > pattern.count('?'):
            answer.append(False)
            continue
        zeros = 0
        possible = True
        for i, ch in enumerate(pattern):
            if ch == '0':
                zeros += 1
            elif ch == '?' and extra:
                zeros += 1
                extra -= 1
            if zeros < prefix[i + 1]:
                possible = False
                break
        answer.append(possible)
    return answer
