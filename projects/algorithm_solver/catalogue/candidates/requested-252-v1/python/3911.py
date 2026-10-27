"""3911. K-th Smallest Remaining Even Integer in Subarray Queries
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/k-th-smallest-remaining-even-integer-in-subarray-queries/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3911.K-th%20Smallest%20Remaining%20Even%20Integer%20in%20Subarray%20Queries/README_EN.md
Complexity: O(n+q log n) time, O(n+q) space.
Strictly increasing positive nums <=1e9; k<=1e9. Counts removed even ranks before kth survivor. Native entry pending.
"""

from __future__ import annotations

def solve(nums, queries):
    evens = []
    prefix = [0]
    for value in nums:
        if value % 2 == 0:
            evens.append(value // 2)
        prefix.append(len(evens))
    answer = []
    for left, right, k in queries:
        start = prefix[left]
        low, high = start, prefix[right + 1]
        while low < high:
            middle = (low + high) // 2
            if evens[middle] - (middle - start) <= k:
                low = middle + 1
            else:
                high = middle
        answer.append(2 * (k + low - start))
    return answer
