"""Hack2Hire 68b996c98c4a0a9996afdd81 (Payment Refund Allocation) over an INFERRED spec; qualification unknown."""


RANK = {'CREDIT': 0, 'CREDIT_CARD': 1, 'PAYPAL': 2}


def solve(transactions, refundAmount):
    refunded = {}
    for row in transactions:
        if row[1] == 'REFUND':
            refunded[row[3]] = refunded.get(row[3], 0) + int(row[5])
    payments = []
    for row in transactions:
        if row[1] == 'PAYMENT':
            rank = RANK.get(row[2], 3)
            payments.append((rank, row[2] if rank == 3 else '', -int(row[4]), row[0], int(row[5]) - refunded.get(row[0], 0)))
    payments.sort()
    remaining, out = refundAmount, []
    for _, _, _, payment_id, available in payments:
        if remaining == 0:
            break
        give = available if available < remaining else remaining
        if give > 0:
            out.append([payment_id, give])
            remaining -= give
    return out


class Solution:
    def allocateRefund(self, transactions, refundAmount):
        return solve(transactions, refundAmount)
