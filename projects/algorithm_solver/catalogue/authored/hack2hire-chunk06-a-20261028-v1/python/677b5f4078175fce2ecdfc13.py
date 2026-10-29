"""Hack2Hire 677b5f4078175fce2ecdfc13 (End Of Day Balance, variant 2 of 2) over an INFERRED spec; qualification unknown."""
import heapq


def solve(transactions):
    balance = {}
    for payer, payee, amount in transactions:
        balance[payer] = balance.get(payer, 0) - amount
        balance[payee] = balance.get(payee, 0) + amount
    names = sorted(balance)  # rank order == name order, so (amount, rank) breaks ties by name
    creditors = [(-balance[name], rank) for rank, name in enumerate(names) if balance[name] > 0]
    debtors = [(balance[name], rank) for rank, name in enumerate(names) if balance[name] < 0]
    heapq.heapify(creditors)
    heapq.heapify(debtors)
    transfers = []
    while creditors:
        credit, creditor = heapq.heappop(creditors)
        debt, debtor = heapq.heappop(debtors)
        amount = min(-credit, -debt)
        transfers.append([names[debtor], names[creditor], amount])
        if -credit > amount:
            heapq.heappush(creditors, (credit + amount, creditor))
        if -debt > amount:
            heapq.heappush(debtors, (debt + amount, debtor))
    return transfers


class Solution:
    def settleBalances(self, transactions):
        return solve(transactions)
