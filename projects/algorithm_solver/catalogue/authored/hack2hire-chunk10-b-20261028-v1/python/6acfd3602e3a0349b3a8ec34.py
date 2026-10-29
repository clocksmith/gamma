"""Hack2Hire 6acfd3602e3a0349b3a8ec34 (Financial Account Ledger, variant 4 of 4) over an INFERRED spec; qualification unknown."""

import heapq


def solve(commands):
    balance, pending = {}, {}
    waiting, stack = {}, {}
    out = []
    seq = 0

    def settle(account, day):
        heap = pending[account]
        while heap and heap[0][0] <= day:
            record = heapq.heappop(heap)[2]
            if not record[2]:
                balance[account] += record[0]
                waiting[account] -= record[0]

    for command in commands:
        f = command.split(' ')
        kind = f[0]
        if kind == 'INIT':
            balance[f[1]] = int(f[2])
            pending[f[1]] = []
            waiting[f[1]] = 0
            stack[f[1]] = []
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
            waiting[account] += record[0]
            stack[account].append(record)
        elif kind == 'BALANCE':
            out.append(balance[account])
        elif kind == 'WITHDRAW':
            amount = int(f[3])
            if amount <= balance[account]:
                balance[account] -= amount
        elif kind == 'TRANSFER':
            target, amount = f[3], int(f[4])
            if target in balance and target != account and amount <= balance[account]:
                balance[account] -= amount
                balance[target] += amount
        elif kind == 'PENDING':
            out.append(waiting[account])
        elif kind == 'CANCEL':
            records = stack[account]
            while records and (records[-1][2] or records[-1][1] <= day):
                records.pop()  # settled or cancelled records never qualify again
            if records:
                record = records.pop()
                record[2] = True
                waiting[account] -= record[0]
    return out


class Solution:
    def processLedger(self, commands):
        return solve(commands)
