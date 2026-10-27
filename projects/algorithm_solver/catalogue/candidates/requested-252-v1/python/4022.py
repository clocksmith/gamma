"""4022. K-th Digit in Infinite String
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/k-th-digit-in-infinite-string/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4022.K-th%20Digit%20in%20Infinite%20String/README_EN.md
Complexity: O(log k) arithmetic steps, O(log k) output-conversion space.
Block 0 omits zero; odd ten-number blocks reverse their integer order, not the digits inside an integer.
"""

from __future__ import annotations

def solve(k):
    if k <= 9:
        return k
    offset = k - 10
    digits, first_block = 2, 1
    while offset >= 90 * first_block * digits:
        offset -= 90 * first_block * digits
        first_block *= 10
        digits += 1
    block, inside = divmod(offset, 10 * digits)
    block += first_block
    number_index, digit_index = divmod(inside, digits)
    value = 10 * block + (number_index if block % 2 == 0 else 9 - number_index)
    return int(str(value)[digit_index])


class Solution:
    def kthDigit(self, k):
        return solve(k)
