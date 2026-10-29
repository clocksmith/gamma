"""Hack2Hire 6a373b366849fecc81442863 (Repair Bootloader Program, variant 2 of 2) over an INFERRED spec; qualification unknown."""


PLUS, NEXT, JUMP = 0, 1, 2
CODE = {'plus': PLUS, 'next': NEXT, 'jump': JUMP}


def solve(instructions):
    n = len(instructions)
    ops, vals = [0] * n, [0] * n
    for i, line in enumerate(instructions):
        op, value = line.split(' ')
        ops[i], vals[i] = CODE[op], int(value)
    preds = [[] for _ in range(n + 1)]
    for i in range(n):
        t = i + vals[i] if ops[i] == JUMP else i + 1
        if 0 <= t <= n:
            preds[t].append(i)
    good = bytearray(n + 1)  # good[i]: the unmodified program reaches index n from i
    good[n] = 1
    stack = [n]
    while stack:
        for i in preds[stack.pop()]:
            if not good[i]:
                good[i] = 1
                stack.append(i)
    seen = bytearray(n)
    i, best = 0, -1
    while 0 <= i < n and not seen[i]:
        seen[i] = 1
        if ops[i] != PLUS:
            t = i + 1 if ops[i] == JUMP else i + vals[i]
            if 0 <= t <= n and good[t] and (best < 0 or i < best):
                best = i
        i = i + vals[i] if ops[i] == JUMP else i + 1
    if best < 0:
        return [-1, 0]
    i = acc = 0
    while i != n:
        op = ops[i]
        if i == best:
            op = NEXT if op == JUMP else JUMP
        if op == JUMP:
            i += vals[i]
        else:
            if op == PLUS:
                acc += vals[i]
            i += 1
    return [best, acc]


class Solution:
    def repairProgram(self, instructions):
        return solve(instructions)
