"""4063. Longest Subarray Divisible by K with At Most One Negation I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/longest-subarray-divisible-by-k-with-at-most-one-negation-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4063.Longest%20Subarray%20Divisible%20by%20K%20with%20At%20Most%20One%20Negation%20I/README_EN.md
Complexity: O(n+DR) expected time, O(min(k,n)+D+k) worst-case space; D distinct doubled-value residues, R distinct prefix residues.
Earliest prefix of each residue dominates later starts. A cursor per doubled-value residue processes each newly discovered prefix residue once, only when the negated index can lie after that prefix. Stored witnesses remain valid for all future ends. Normalize negative remainders in JavaScript. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, k):
    first = {0: 0}
    order = [(0, 0)]
    cursor = {}
    changed = {}
    prefix = answer = 0
    for index, value in enumerate(nums):
        adjustment = (2*value) % k
        if adjustment:
            p = cursor.get(adjustment, 0)
            while p < len(order):
                residue, left = order[p]
                wanted = (residue+adjustment) % k
                if wanted not in changed or left < changed[wanted]:
                    changed[wanted] = left
                p += 1
            cursor[adjustment] = p
        prefix = (prefix+value) % k
        left = min(first.get(prefix, index+1), changed.get(prefix, index+1))
        answer = max(answer, index+1-left)
        if prefix not in first:
            first[prefix] = index+1
            order.append((prefix, index+1))
    return answer


class Solution:
    def longestSubarray(self, nums, k):
        return solve(nums, k)
