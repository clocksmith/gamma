"""Hack2Hire 67fc7863216af53465a7221c (Work Schedule) over an INFERRED spec; qualification unknown."""


def solve(pattern, workHours, dayHours):
    chars = list(pattern)
    slots = [i for i, ch in enumerate(chars) if ch == '?']
    need = workHours - sum(int(ch) for ch in chars if ch != '?')
    result = []
    if need < 0 or need > len(slots) * dayHours:
        return result

    def fill(index, remaining):
        if index == len(slots):
            if remaining == 0:
                result.append(''.join(chars))
            return
        left = len(slots) - index - 1
        for digit in range(min(dayHours, remaining) + 1):
            if remaining - digit <= left * dayHours:
                chars[slots[index]] = str(digit)
                fill(index + 1, remaining - digit)

    fill(0, need)
    return result


class Solution:
    def findSchedules(self, pattern, workHours, dayHours):
        return solve(pattern, workHours, dayHours)
