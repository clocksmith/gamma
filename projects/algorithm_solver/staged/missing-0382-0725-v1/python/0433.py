"""433. Minimum Genetic Mutation."""

from collections import deque

def solve(startGene: str, endGene: str, bank: list[str]) -> int:
    if startGene == endGene:
        return 0
    available = set(bank)
    if endGene not in available:
        return -1
    queue = deque([(startGene, 0)])
    available.discard(startGene)
    while queue:
        gene, distance = queue.popleft()
        for i in range(len(gene)):
            for char in 'ACGT':
                candidate = gene[:i] + char + gene[i + 1:]
                if candidate in available:
                    if candidate == endGene:
                        return distance + 1
                    available.remove(candidate)
                    queue.append((candidate, distance + 1))
    return -1


class Solution:
    def minMutation(self, startGene: str, endGene: str, bank: list[str]) -> int:
        return solve(startGene, endGene, bank)
