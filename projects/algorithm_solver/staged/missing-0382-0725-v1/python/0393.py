"""393. UTF-8 Validation. Validate the problem's byte-prefix structure, not Unicode scalar canonicality."""

def solve(data: list[int]) -> bool:
    remaining = 0
    for value in data:
        value &= 255
        if remaining:
            if value >> 6 != 2:
                return False
            remaining -= 1
        elif value < 128:
            continue
        elif value >> 5 == 6:
            remaining = 1
        elif value >> 4 == 14:
            remaining = 2
        elif value >> 3 == 30:
            remaining = 3
        else:
            return False
    return remaining == 0


class Solution:
    def validUtf8(self, data: list[int]) -> bool:
        return solve(data)
