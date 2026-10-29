"""Hack2Hire 6897c08aa543d38b79706ca6 (Cross-Day User Trust Scoring) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class PurchaseAnalyzer:
    def __init__(self, logsDay1, logsDay2):
        days = {}
        types = {}
        for bit, logs in ((1, logsDay1), (2, logsDay2)):
            for row in logs:
                user = row[1]
                days[user] = days.get(user, 0) | bit
                kinds = types.get(user)
                if kinds is None:
                    kinds = set()
                    types[user] = kinds
                kinds.add(row[2])
        self.users = sorted(u for u in days if days[u] == 3 and len(types[u]) >= 2)

    def crossDayDiverseUsers(self):
        return list(self.users)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PurchaseAnalyzer' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = PurchaseAnalyzer(*argument_lists[0])
    allowed = {'crossDayDiverseUsers'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
