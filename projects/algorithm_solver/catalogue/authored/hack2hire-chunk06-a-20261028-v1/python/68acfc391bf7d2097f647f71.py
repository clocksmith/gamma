"""Hack2Hire 68acfc391bf7d2097f647f71 (Find Users with Valid Login Sessions) over an INFERRED spec; qualification unknown."""


def solve(logs, maxTime):
    open_since, valid = {}, set()
    for line in logs:
        user, action, stamp = line.split(' ')
        t = int(stamp)
        if action == 'signin':
            open_since[user] = t
        else:
            start = open_since.pop(user, None)
            if start is not None and t - start <= maxTime:
                valid.add(user)
    return sorted(valid)


class Solution:
    def findValidUsers(self, logs, maxTime):
        return solve(logs, maxTime)
