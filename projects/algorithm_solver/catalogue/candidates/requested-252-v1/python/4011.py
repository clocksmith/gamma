"""4011. Count Subarrays With Even Odd Ratio I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-subarrays-with-even-odd-ratio-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4011.Count%20Subarrays%20With%20Even%20Odd%20Ratio%20I/README_EN.md
Complexity: O(n log n) time, O(n) space.
Map odds to +a and evens to -b. Nonnegative interval sums automatically exclude all-even nonempty intervals. Counts and prefix sums stay within Number exact range. Inputs preserved; native method unconfirmed.
"""

from __future__ import annotations

def solve(nums, a, b):
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] + (a if value % 2 else -b))
    rank = {value: i + 1 for i, value in enumerate(sorted(set(prefix)))}
    tree = [0] * (len(rank) + 1)
    answer = 0
    for value in prefix:
        i = rank[value]
        while i:
            answer += tree[i]
            i -= i & -i
        i = rank[value]
        while i < len(tree):
            tree[i] += 1
            i += i & -i
    return answer
