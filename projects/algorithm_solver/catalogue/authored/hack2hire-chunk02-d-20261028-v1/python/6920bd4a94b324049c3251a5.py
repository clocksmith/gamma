"""Hack2Hire 6920bd4a94b324049c3251a5 (Expense System, level 2) over an INFERRED spec; qualification unknown."""
FIELDS = {'expense_id': 0, 'trip_id': 1, 'amount': 2, 'expense_type': 3, 'vendor_type': 4, 'vendor_name': 5}


def _cents(text):
    whole, _, frac = text.partition('.')
    return int(whole) * 100 + int((frac + '00')[:2])


def _holds(lhs, op, rhs):
    if op == '<':
        return lhs < rhs
    if op == '<=':
        return lhs <= rhs
    if op == '>':
        return lhs > rhs
    if op == '>=':
        return lhs >= rhs
    if op == '==':
        return lhs == rhs
    return lhs != rhs


def solve(rules, expenses):
    amounts = [_cents(e[2]) for e in expenses]
    result = []
    for kind, rule_id, field, op, value, cond_field, cond_value in rules:
        column = FIELDS[field]
        rhs = _cents(value) if field == 'amount' else value
        cond = FIELDS[cond_field] if cond_field else -1
        trips = {}
        for index, expense in enumerate(expenses):
            if cond >= 0 and expense[cond] != cond_value:
                continue
            if kind == 'trip':
                trips[expense[1]] = trips.get(expense[1], 0) + amounts[index]
                continue
            lhs = amounts[index] if column == 2 else expense[column]
            if not _holds(lhs, op, rhs):
                result.append([rule_id, expense[0]])
        for trip, total in trips.items():
            if not _holds(total, op, rhs):
                result.append([rule_id, trip])
    return result


class Solution:
    def findViolations(self, rules, expenses):
        return solve(rules, expenses)
