"""Hack2Hire 6907b46fe1919109b6df119a (Pandigital Sum) over an INFERRED spec; qualification unknown."""


COLUMNS = ((2, 5, 8), (1, 4, 7), (0, 3, 6))


def solve(pattern):
    fixed = [0 if c == '?' else ord(c) - 48 for c in pattern]
    used = 0
    for d in fixed:
        if d:
            used |= 1 << d

    def options(position, mask):
        if fixed[position]:
            return (fixed[position],)
        return tuple(d for d in range(1, 10) if not mask >> d & 1)

    def go(column, carry, mask):
        if column == 3:
            return 1 if carry == 0 else 0
        a_pos, b_pos, s_pos = COLUMNS[column]
        total = 0
        for a in options(a_pos, mask):
            mask_a = mask | 1 << a
            for b in options(b_pos, mask_a):
                if b == a:
                    continue
                mask_b = mask_a | 1 << b
                t = a + b + carry
                d = t % 10
                if d == 0 or d == a or d == b:
                    continue
                if fixed[s_pos]:
                    if fixed[s_pos] != d:
                        continue
                elif mask_b >> d & 1:
                    continue
                total += go(column + 1, t // 10, mask_b | 1 << d)
        return total
    return go(0, 0, used)


class Solution:
    def countPandigitalSums(self, pattern):
        return solve(pattern)
