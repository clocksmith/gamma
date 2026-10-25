class ProbabilityHeap:
    def __init__(self):
        self.items = []

    def higher(self, first, second) -> bool:
        return first[0] > second[0] or (first[0] == second[0] and first[1] < second[1])

    def push(self, item) -> None:
        self.items.append(item)
        index = len(self.items) - 1
        while index > 0:
            parent = (index - 1) // 2
            if not self.higher(self.items[index], self.items[parent]):
                break
            self.items[index], self.items[parent] = self.items[parent], self.items[index]
            index = parent

    def pop(self):
        result = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            index = 0
            while True:
                left = 2 * index + 1
                if left >= len(self.items):
                    break
                right = left + 1
                child = left
                if right < len(self.items) and self.higher(self.items[right], self.items[left]):
                    child = right
                if not self.higher(self.items[child], self.items[index]):
                    break
                self.items[index], self.items[child] = self.items[child], self.items[index]
                index = child
        return result


class Solution:
    def maxProbability(self, n: int, edges: list[list[int]], succProb: list[float], start_node: int, end_node: int) -> float:
        neighbors = [[] for _ in range(n)]
        for index, (first, second) in enumerate(edges):
            probability = succProb[index]
            neighbors[first].append((second, probability))
            neighbors[second].append((first, probability))
        best = [0.0] * n
        best[start_node] = 1.0
        heap = ProbabilityHeap()
        heap.push((1.0, start_node))
        while heap.items:
            probability, node = heap.pop()
            if probability < best[node]:
                continue
            if node == end_node:
                return probability
            for neighbor, edge_probability in neighbors[node]:
                candidate = probability * edge_probability
                if candidate > best[neighbor]:
                    best[neighbor] = candidate
                    heap.push((candidate, neighbor))
        return 0.0
