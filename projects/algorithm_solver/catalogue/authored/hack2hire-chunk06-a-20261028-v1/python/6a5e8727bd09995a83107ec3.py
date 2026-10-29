"""Hack2Hire 6a5e8727bd09995a83107ec3 (Find Redeemable Offers) over an INFERRED spec; qualification unknown."""


def solve(offers, events, processingTime):
    window = {}
    for offer_id, start, end, limit in offers:
        window[offer_id] = (int(start), int(end), int(limit))
    counts, users = {}, set()
    for user, timestamp, action, offer_id in events:
        users.add(user)
        info = window.get(offer_id)
        if info is None:
            continue
        t = int(timestamp)
        if t > processingTime or t < info[0] or t > info[1]:
            continue
        key = (user, offer_id)
        count = counts.get(key, 0)
        if action == 'redeem':
            if count < info[2]:
                counts[key] = count + 1
        elif count > 0:
            counts[key] = count - 1
    active = [(row[0], window[row[0]][2]) for row in offers if window[row[0]][0] <= processingTime <= window[row[0]][1]]
    return [[user, [oid for oid, limit in active if counts.get((user, oid), 0) < limit]] for user in sorted(users)]


class Solution:
    def redeemableOffers(self, offers, events, processingTime):
        return solve(offers, events, processingTime)
