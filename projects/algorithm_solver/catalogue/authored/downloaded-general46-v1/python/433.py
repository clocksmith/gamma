"""433. Minimum Genetic Mutation (Medium).

Specification: https://leetcode.com/problems/minimum-genetic-mutation/description/
"""


def solve(startGene: str, endGene: str, bank: list[str]) -> int:
    bank_set = set(bank)
    if endGene not in bank_set:
        return -1
    letters = ['A', 'C', 'G', 'T']
    queue = [startGene]
    visited = {startGene}
    steps = 0
    while queue:
        next_queue = []
        for gene in queue:
            if gene == endGene:
                return steps
            for i in range(len(gene)):
                for letter in letters:
                    candidate = gene[:i] + letter + gene[i + 1:]
                    if candidate in bank_set and candidate not in visited:
                        visited.add(candidate)
                        next_queue.append(candidate)
        queue = next_queue
        steps += 1
    return -1


class Solution:
    def minMutation(self, startGene: str, endGene: str, bank: list[str]) -> int:
        return solve(startGene, endGene, bank)
