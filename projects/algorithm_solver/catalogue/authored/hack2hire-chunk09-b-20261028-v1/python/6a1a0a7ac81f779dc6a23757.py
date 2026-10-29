"""Hack2Hire 6a1a0a7ac81f779dc6a23757 (Credit Card Fraud Detection, variant 3 of 3) over an INFERRED spec; qualification unknown."""


def solve(requests, rules, fraudReports):
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
    card_of = {}
    for s in requests:
        ts, uid, amount, card, merchant = s.split(',')
        parsed.append((int(ts), uid, int(amount), card, merchant))
        card_of[uid] = card
    blocked_after = {}
    for report in fraudReports:
        ts, uid = report.split(',')
        card = card_of[uid]
        if card not in blocked_after or int(ts) < blocked_after[card]:
            blocked_after[card] = int(ts)
    parsed.sort(key=lambda row: row[0])
    out = []
    for ts, uid, amount, card, merchant in parsed:
        bad = (card in cards or merchant in merchants or (limit is not None and amount > limit)
               or (card in blocked_after and ts > blocked_after[card]))
        out.append([uid, 'DECLINE' if bad else 'APPROVE'])
    return out


class Solution:
    def processRequests(self, requests, rules, fraudReports):
        return solve(requests, rules, fraudReports)
