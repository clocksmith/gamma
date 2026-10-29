"""Hack2Hire 6a373b356849fecc81442862 (Repair Bootloader Program, variant 1 of 2) over an INFERRED spec; qualification unknown."""


PLUS, NEXT, JUMP = 0, 1, 2
CODE = {'plus': PLUS, 'next': NEXT, 'jump': JUMP}


def solve(instructions):
    n = len(instructions)
    ops, vals = [0] * n, [0] * n
    for i, line in enumerate(instructions):
        op, value = line.split(' ')
        ops[i], vals[i] = CODE[op], int(value)
    seen = bytearray(n)
    i = acc = 0
    while 0 <= i < n:
        if seen[i]:
            return [i, acc]
        seen[i] = 1
        if ops[i] == JUMP:
            i += vals[i]
        else:
            if ops[i] == PLUS:
                acc += vals[i]
            i += 1
    return [-1, acc]


class Solution:
    def findLoop(self, instructions):
        return solve(instructions)
