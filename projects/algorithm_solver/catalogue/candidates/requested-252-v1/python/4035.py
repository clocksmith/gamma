"""4035. Maximum Valid Split Positions I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-valid-split-positions-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4035.Maximum%20Valid%20Split%20Positions%20I/README_EN.md
Complexity: O(n + log(M) log(n)) GCD operations, O(n) space; each GCD costs O(log(M)).
Only prefix/suffix-GCD change indices can improve the score. A deleted leaf is represented by neutral zero. Prefix/suffix descent locates all valid boundaries; an interior zero duplicates exactly one boundary, which is subtracted. Inputs preserved.
"""

from __future__ import annotations
from math import gcd

def solve(nums):
    n = len(nums)
    size = 1
    while size < n:
        size *= 2
    tree = [0] * (2 * size)
    tree[size:size+n] = nums
    for i in range(size-1, 0, -1):
        tree[i] = gcd(tree[i*2], tree[i*2+1])
    candidates = set()
    current = 0
    for i, x in enumerate(nums):
        following = gcd(current, x)
        if following != current:
            candidates.add(i)
        current = following
    current = 0
    for i in range(n-1, -1, -1):
        following = gcd(current, nums[i])
        if following != current:
            candidates.add(i)
        current = following
    def put(index, value):
        p = size + index
        tree[p] = value
        while p > 1:
            p //= 2
            tree[p] = gcd(tree[2*p], tree[2*p+1])
    def score(deleted=-1):
        target = tree[1]
        p, prefix = 1, 0
        while p < size:
            q = p * 2
            combined = gcd(prefix, tree[q])
            if combined == target:
                p = q
            else:
                prefix, p = combined, q + 1
        first = p - size
        p, suffix = 1, 0
        while p < size:
            q = p * 2 + 1
            combined = gcd(suffix, tree[q])
            if combined == target:
                p = q
            else:
                suffix, p = combined, q - 1
        last = p - size
        return max(0, last-first) - int(first < deleted < last)
    answer = score()
    for index in candidates:
        put(index, 0)
        answer = max(answer, score(index))
        put(index, nums[index])
    return answer
