"""2073. Time Needed to Buy Tickets (Easy).

Specification: https://leetcode.com/problems/time-needed-to-buy-tickets/description/
"""


def solve(tickets: list[int], k: int) -> int:
    """O(n) time, O(1) space; count turns before the kth buyer finishes; preserve tickets."""
    target = tickets[k]
    seconds = 0
    for index, count in enumerate(tickets):
        limit = target if index <= k else target - 1
        seconds += min(count, limit)
    return seconds


class Solution:
    def timeRequiredToBuy(self, tickets: list[int], k: int) -> int:
        return solve(tickets, k)
