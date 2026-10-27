"""4049. Count Values With Equally Spaced Occurrences II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/count-values-with-equally-spaced-occurrences-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4049.Count%20Values%20With%20Equally%20Spaced%20Occurrences%20II/README_EN.md
Complexity: O(n) expected time, O(U) space.
Counts all occurrences; at least three are required. Input preserved.
"""

from __future__ import annotations

def solve(nums):
    records = {}
    for index, value in enumerate(nums):
        if value not in records:
            records[value] = [1, index, 0, True]
        else:
            record = records[value]
            gap = index - record[1]
            if record[0] == 1:
                record[2] = gap
            elif gap != record[2]:
                record[3] = False
            record[0] += 1
            record[1] = index
    return sum((count == 3 if False else count >= 3) and valid
               for count, _, _, valid in records.values())


class Solution:
    def countSpecialIntegers(self, nums):
        return solve(nums)
