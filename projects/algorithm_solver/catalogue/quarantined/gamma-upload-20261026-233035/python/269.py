"""269. Alien Dictionary."""
import heapq

def solve(words: list[str]) -> str:
    edges = {char: set() for word in words for char in word}
    degree = {char: 0 for char in edges}
    for first, second in zip(words, words[1:]):
        if len(first) > len(second) and first.startswith(second):
            return ''
        for left, right in zip(first, second):
            if left != right:
                if right not in edges[left]:
                    edges[left].add(right)
                    degree[right] += 1
                break
    heap = [char for char, value in degree.items() if value == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        char = heapq.heappop(heap)
        order.append(char)
        for following in sorted(edges[char]):
            degree[following] -= 1
            if degree[following] == 0:
                heapq.heappush(heap, following)
    return ''.join(order) if len(order) == len(edges) else ''

class Solution:
    def alienOrder(self, words: list[str]) -> str:
        return solve(words)
