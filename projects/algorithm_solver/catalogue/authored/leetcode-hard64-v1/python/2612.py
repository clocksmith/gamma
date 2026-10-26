"""2612. Minimum Reverse Operations: breadth-first search with parity-preserving successor deletion."""


def solve(n: int, p: int, banned: list[int], k: int) -> list[int]:
    """O(n * alpha(n) + len(banned)) amortized time and O(n) space. Inputs are preserved."""
    successor = list(range(n + 2))

    def find(index):
        root = index
        while successor[root] != root:
            root = successor[root]
        while successor[index] != index:
            following = successor[index]
            successor[index] = root
            index = following
        return root

    for index in banned:
        successor[index] = find(index + 2)
    successor[p] = find(p + 2)
    answer = [-1] * n
    answer[p] = 0
    queue = [p]
    head = 0
    while head < len(queue):
        current = queue[head]
        head += 1
        minimum = 2 * max(0, current - k + 1) + k - 1 - current
        maximum = 2 * min(current, n - k) + k - 1 - current
        following = find(minimum)
        while following <= maximum:
            answer[following] = answer[current] + 1
            queue.append(following)
            successor[following] = find(following + 2)
            following = find(following)
    return answer


class Solution:
    def minReverseOperations(self, n: int, p: int, banned: list[int], k: int) -> list[int]:
        return solve(n, p, banned, k)
