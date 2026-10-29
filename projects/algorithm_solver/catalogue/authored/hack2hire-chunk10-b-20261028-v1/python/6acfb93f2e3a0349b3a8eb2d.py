"""Hack2Hire 6acfb93f2e3a0349b3a8eb2d (Financial Account Ledger, variant 1 of 4) over an INFERRED spec; qualification unknown."""

import heapq


def solve(commands):
    balance, pending = {}, {}
    out = []
    seq = 0

    def settle(account, day):
        heap = pending[account]
        while heap and heap[0][0] <= day:
            record = heapq.heappop(heap)[2]
            if not record[2]:
                balance[account] += record[0]

    for command in commands:
        f = command.split(' ')
        kind = f[0]
        if kind == 'INIT':
            balance[f[1]] = int(f[2])
            pending[f[1]] = []
            continue
        day, account = int(f[1]), f[2]
        if account not in balance:
            if kind in ('BALANCE', 'PENDING'):
                out.append(-1)
            continue
        settle(account, day)
        if kind == 'FUND':
            record = [int(f[3]), day + int(f[4]), False]  # amount, settle day, cancelled
            seq += 1
            heapq.heappush(pending[account], (record[1], seq, record))
        elif kind == 'BALANCE':
            out.append(balance[account])
    return out


class Solution:
    def processLedger(self, commands):
        return solve(commands)
