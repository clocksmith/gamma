"""3213. Construct String with Minimum Cost.

Aho-Corasick matches feed a shortest-prefix dynamic program; O(26*S+N+Z) time and O(26*S+N) space, Z matched words. Inputs are preserved.
"""

from collections import deque


def solve(target: str, words: list[str], costs: list[int]) -> int:
    transitions = [[-1] * 26]
    failure, output, depth, price = [0], [0], [0], [float('inf')]
    for word, cost in zip(words, costs):
        node = 0
        for character in word:
            letter = ord(character) - 97
            child = transitions[node][letter]
            if child == -1:
                child = len(transitions)
                transitions[node][letter] = child
                transitions.append([-1] * 26)
                failure.append(0)
                output.append(0)
                depth.append(depth[node] + 1)
                price.append(float('inf'))
            node = child
        price[node] = min(price[node], cost)
    queue = deque()
    for letter in range(26):
        child = transitions[0][letter]
        if child == -1:
            transitions[0][letter] = 0
        else:
            queue.append(child)
    while queue:
        node = queue.popleft()
        fallback = failure[node]
        output[node] = fallback if price[fallback] != float('inf') else output[fallback]
        for letter in range(26):
            child = transitions[node][letter]
            if child == -1:
                transitions[node][letter] = transitions[fallback][letter]
            else:
                failure[child] = transitions[fallback][letter]
                queue.append(child)
    best = [0] + [float('inf')] * len(target)
    node = 0
    for end, character in enumerate(target, 1):
        node = transitions[node][ord(character) - 97]
        match = node if price[node] != float('inf') else output[node]
        while match:
            best[end] = min(best[end], best[end - depth[match]] + price[match])
            match = output[match]
    return -1 if best[-1] == float('inf') else best[-1]


class Solution:
    def minimumCost(self, target: str, words: list[str], costs: list[int]) -> int:
        return solve(target, words, costs)
