"""Original LeetCode 710 candidate; qualification unknown."""

import random

class Solution:
    def __init__(self, n, blacklist):
        blocked = set(blacklist)
        self.limit = n - len(blacklist)
        self.remap, high = {}, n - 1
        for value in blacklist:
            if value < self.limit:
                while high in blocked: high -= 1
                self.remap[value] = high
                high -= 1
    def pick(self):
        ticket = random.randrange(self.limit)
        return self.remap.get(ticket, ticket)


def solve(operations, arguments):
    instance = Solution(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
