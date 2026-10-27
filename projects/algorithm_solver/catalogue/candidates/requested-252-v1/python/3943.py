"""3943. Number of Pairs After Increment
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/number-of-pairs-after-increment/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3943.Number%20of%20Pairs%20After%20Increment/README_EN.md
Complexity: O(m+q*(sqrt(m)+d*sqrt(m))) time, O(m) space; d<=5.
Range additions update internal copy only; later queries see updates. Multiplicities count. Number safe for <=50000 increments of <=1e5. Native name pending.
"""

from __future__ import annotations
from collections import Counter
from math import isqrt

def solve(nums1, nums2, queries):
    values = nums2.copy()
    width = max(1, isqrt(len(values)))
    blocks = (len(values) + width - 1) // width
    lazy = [0] * blocks
    frequency = [{} for _ in range(blocks)]
    for index, value in enumerate(values):
        counts = frequency[index // width]
        counts[value] = counts.get(value, 0) + 1
    first_counts = Counter(nums1)
    answer = []
    for query in queries:
        if query[0] == 1:
            _, left, right, increment = query
            for block in range(left // width, right // width + 1):
                start = block * width
                end = min(len(values), start + width)
                if left <= start and end - 1 <= right:
                    lazy[block] += increment
                    continue
                counts = frequency[block]
                for index in range(max(left, start), min(right + 1, end)):
                    old = values[index]
                    counts[old] -= 1
                    if counts[old] == 0:
                        del counts[old]
                    values[index] += increment
                    counts[values[index]] = counts.get(values[index], 0) + 1
        else:
            total = query[1]
            pairs = 0
            for block in range(blocks):
                for value, multiplicity in first_counts.items():
                    pairs += multiplicity * frequency[block].get(total - value - lazy[block], 0)
            answer.append(pairs)
    return answer
