"""Hack2Hire 6976e8995ed12b33b05f10f7 (Match Payment to Invoice, v2); INFERRED spec; qualification unknown."""
MARKER = 'paying off:'
ID_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')


def reference_id(memo):
    at = memo.find(MARKER)
    if at < 0: return None
    start = end = at + len(MARKER)
    while end < len(memo) and memo[end] in ID_CHARS: end += 1
    return memo[start:end] if end > start else None


def solve(payments, invoices):
    parsed = [record.split(',') for record in invoices]
    known = {p[0] for p in parsed}
    buckets = {}
    for invoice_id, amount, due in sorted(parsed, key=lambda p: (p[2], p[0])):
        buckets.setdefault(int(amount), [[], 0])[0].append(invoice_id)
    used, out = set(), []
    for record in payments:
        payment_id, amount, memo = record.split(',', 2)
        target = reference_id(memo)
        match = None
        if target in known and target not in used: match = target
        else:
            bucket = buckets.get(int(amount))
            if bucket is not None:
                ids = bucket[0]
                while bucket[1] < len(ids) and ids[bucket[1]] in used: bucket[1] += 1
                if bucket[1] < len(ids): match = ids[bucket[1]]
        if match is not None: used.add(match)
        out.append([payment_id, match])
    return out


class Solution:
    def matchPayments(self, payments, invoices):
        return solve(payments, invoices)
