"""3327. Check if DFS Strings Are Palindromes: iterative postorder intervals and exact Manacher palindrome radii."""


def solve(parent: list[int], s: str) -> list[bool]:
    """O(n) time and O(n) auxiliary space. Inputs are preserved."""
    n = len(parent)
    children = [[] for _ in range(n)]
    for node in range(1, n):
        children[parent[node]].append(node)
    left = [0] * n
    right = [0] * n
    text = []
    stack = [(0, False)]
    while stack:
        node, exiting = stack.pop()
        if exiting:
            text.append(s[node])
            right[node] = len(text)
        else:
            left[node] = len(text)
            stack.append((node, True))
            for child in reversed(children[node]):
                stack.append((child, False))
    odd = [0] * n
    start, end = 0, -1
    for center in range(n):
        radius = 1 if center > end else min(odd[start + end - center], end - center + 1)
        while center - radius >= 0 and center + radius < n and text[center - radius] == text[center + radius]:
            radius += 1
        odd[center] = radius
        if center + radius - 1 > end:
            start, end = center - radius + 1, center + radius - 1
    even = [0] * n
    start, end = 0, -1
    for center in range(n):
        radius = 0 if center > end else min(even[start + end - center + 1], end - center + 1)
        while center - radius - 1 >= 0 and center + radius < n and text[center - radius - 1] == text[center + radius]:
            radius += 1
        even[center] = radius
        if center + radius - 1 > end:
            start, end = center - radius, center + radius - 1
    answer = []
    for begin, finish in zip(left, right):
        length = finish - begin
        center = (begin + finish) // 2
        answer.append(odd[center] >= length // 2 + 1 if length % 2 else even[center] >= length // 2)
    return answer


class Solution:
    def findAnswer(self, parent: list[int], s: str) -> list[bool]:
        return solve(parent, s)
