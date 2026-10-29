"""Hack2Hire 697699035ed12b33b05f0f4e (Match Payment to Invoice, v1); INFERRED spec; qualification unknown."""
MARKER = 'paying off:'
ID_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def reference_id(memo):
    at = memo.find(MARKER)
    if at < 0: return None
    start = end = at + len(MARKER)
    while end < len(memo) and memo[end] in ID_CHARS: end += 1
    return memo[start:end] if end > start else None


def solve(payments, invoices):
    known = {record.split(',', 1)[0] for record in invoices}
    out = []
    for record in payments:
        payment_id, _, memo = record.split(',', 2)
        target = reference_id(memo)
        out.append([payment_id, target if target in known else None])
    return out


class Solution:
    def matchPaymentsByMemo(self, payments, invoices):
        return solve(payments, invoices)
