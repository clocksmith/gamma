"""Hack2Hire 6981207ff8f2604d5eed002c (Account Balance Processor, level 3) over an INFERRED spec; qualification unknown."""

LEVEL = 3


def solve(logs):
    records = [line.split(',') for line in logs]
    if LEVEL >= 2:
        seen, kept = set(), []
        for record in records:
            if record[0] not in seen:
                seen.add(record[0])
                kept.append(record)
        records = kept
    balance = {}
    for record in records:
        balance.setdefault(record[1], 0)
    rejected = []
    if LEVEL == 3:
        records = sorted(records, key=lambda record: int(record[3]))
    for txn, account, amount, _ in records:
        value = int(amount)
        if LEVEL == 3 and balance[account] + value < 0:
            rejected.append(txn)
            continue
        balance[account] += value
    rows = [[account, balance[account]] for account in sorted(balance)]
    return [rows, rejected] if LEVEL == 3 else rows


class Solution:
    def processLogs(self, logs):
        return solve(logs)
