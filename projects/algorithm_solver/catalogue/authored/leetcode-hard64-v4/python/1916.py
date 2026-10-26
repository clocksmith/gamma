"""1916. Count Ways to Build Rooms in an Ant Colony."""


def solve(prevRoom: list[int]) -> int:
    """Tree hook-length formula with iterative subtree sizes; O(n+log MOD) modular operations, O(n) space. Inputs are preserved."""
    modulus = 1_000_000_007
    size = len(prevRoom)
    children = [[] for _ in range(size)]
    for node in range(1, size):
        children[prevRoom[node]].append(node)
    order = [0]
    for node in order:
        order.extend(children[node])
    subtree = [1] * size
    for node in reversed(order[1:]):
        subtree[prevRoom[node]] += subtree[node]
    factorial = 1
    denominator = 1
    for index, amount in enumerate(subtree, 1):
        factorial = factorial * index % modulus
        denominator = denominator * amount % modulus
    return factorial * pow(denominator, modulus - 2, modulus) % modulus


class Solution:
    def waysToBuildRooms(self, prevRoom: list[int]) -> int:
        return solve(prevRoom)
