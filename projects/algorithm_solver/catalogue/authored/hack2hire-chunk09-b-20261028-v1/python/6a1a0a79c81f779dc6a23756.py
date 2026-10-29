"""Hack2Hire 6a1a0a79c81f779dc6a23756 (Credit Card Fraud Detection, variant 2 of 3) over an INFERRED spec; qualification unknown."""


def solve(requests, rules):
    cards, merchants = set(), set()
    limit = None
    for rule in rules:
        field, value = rule.split(',')
        if field == 'card_number':
            cards.add(value)
        elif field == 'merchant':
            merchants.add(value)
        elif limit is None or int(value) < limit:
            limit = int(value)
    parsed = []
    for s in requests:
        ts, uid, amount, card, merchant = s.split(',')
        parsed.append((int(ts), uid, int(amount), card, merchant))
    parsed.sort(key=lambda row: row[0])
    out = []
    for _, uid, amount, card, merchant in parsed:
        bad = card in cards or merchant in merchants or (limit is not None and amount > limit)
        out.append([uid, 'DECLINE' if bad else 'APPROVE'])
    return out


class Solution:
    def processRequests(self, requests, rules):
        return solve(requests, rules)
