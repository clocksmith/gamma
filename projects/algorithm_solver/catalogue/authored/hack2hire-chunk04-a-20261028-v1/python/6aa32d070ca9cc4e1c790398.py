"""Hack2Hire 6aa32d070ca9cc4e1c790398 (Referral Credit Tracker, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class AccountCreditTracker:
    def __init__(self):
        self.totals = []

    def addAccount(self, credit):
        self.totals.append(credit)
        self._touch(len(self.totals) - 1)
        return len(self.totals) - 1

    def addAccountWithReferral(self, credit, referrerId):
        self.totals[referrerId] += credit
        self._touch(referrerId)
        return self.addAccount(credit)

    def getTotalCredit(self, accountId):
        return self.totals[accountId]

    def _touch(self, account):
        pass


def solve(operation_names, argument_lists):
    if operation_names[0] != 'AccountCreditTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = AccountCreditTracker(*argument_lists[0])
    allowed = ['addAccount', 'addAccountWithReferral', 'getTotalCredit']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in [] else value)
    return result
