"""Hack2Hire 69c84ccb21f6ab4226966c5a (Guess Number II) over an INFERRED spec; qualification unknown."""

def solve(target):
    lo, hi, log, previous = 0, 999, [], None
    while True:
        query = lo if lo == hi or len(log) % 2 == 0 else hi
        log.append(query)
        if query == target:
            return log
        if previous is None:
            answer = 'First'
        else:
            a, b = abs(query - target), abs(previous - target)
            answer = 'Hotter' if a < b else 'Colder' if a > b else 'Same'
        if query == lo:
            lo += 1
        else:
            hi -= 1
        if answer == 'Same':
            lo = hi = (query + previous) // 2
        elif answer != 'First':
            twice_mid = query + previous
            if (answer == 'Hotter') == (query > previous):
                lo = max(lo, twice_mid // 2 + 1)
            else:
                hi = min(hi, (twice_mid + 1) // 2 - 1)
        previous = query


class Solution:
    def hotColdTranscript(self, target):
        return solve(target)
