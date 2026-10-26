"""1601. Maximum Number of Achievable Transfer Requests: enumerate nontrivial request subsets and check net balances; O((n+q)*2^q) time and O(n+q) space."""


def solve(n: int, requests: list[list[int]]) -> int:
    transfers = [(first, second) for first, second in requests if first != second]
    automatic = len(requests) - len(transfers)
    best = 0
    for mask in range(1 << len(transfers)):
        count = mask.bit_count()
        if count <= best:
            continue
        balance = [0] * n
        for index, (first, second) in enumerate(transfers):
            if mask & (1 << index):
                balance[first] -= 1
                balance[second] += 1
        if all(value == 0 for value in balance):
            best = count
    return automatic + best


class Solution:
    def maximumRequests(self, n: int, requests: list[list[int]]) -> int:
        return solve(n, requests)
