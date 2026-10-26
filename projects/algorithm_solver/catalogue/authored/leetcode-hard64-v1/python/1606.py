"""1606. Find Servers That Handled Most Number of Requests: release-time heap and Fenwick order statistics for free servers."""

from heapq import heappop, heappush


def solve(k: int, arrival: list[int], load: list[int]) -> list[int]:
    """O((n + k) * log(k + 1)) time and O(k) space. Inputs are preserved."""
    tree = [0] + [index & -index for index in range(1, k + 1)]

    def add(server, change):
        index = server + 1
        while index <= k:
            tree[index] += change
            index += index & -index

    def prefix(length):
        total = 0
        while length:
            total += tree[length]
            length -= length & -length
        return total

    def select(order):
        index = 0
        step = 1 << (k.bit_length() - 1)
        while step:
            following = index + step
            if following <= k and tree[following] < order:
                order -= tree[following]
                index = following
            step >>= 1
        return index

    busy = []
    handled = [0] * k
    for request, time in enumerate(arrival):
        while busy and busy[0][0] <= time:
            _, server = heappop(busy)
            add(server, 1)
        available = prefix(k)
        if available == 0:
            continue
        before = prefix(request % k)
        server = select(before + 1 if before < available else 1)
        add(server, -1)
        handled[server] += 1
        heappush(busy, (time + load[request], server))
    best = max(handled)
    return [server for server, count in enumerate(handled) if count == best]


class Solution:
    def busiestServers(self, k: int, arrival: list[int], load: list[int]) -> list[int]:
        return solve(k, arrival, load)
