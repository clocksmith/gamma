class DisjointSet:
    def __init__(self, count: int):
        self.parent = list(range(count))
        self.size = [1] * count
        self.minimum = list(range(count))
        self.components = count

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, first: int, second: int) -> bool:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root == second_root:
            return False
        if self.size[first_root] < self.size[second_root]:
            first_root, second_root = second_root, first_root
        self.parent[second_root] = first_root
        self.size[first_root] += self.size[second_root]
        self.minimum[first_root] = min(self.minimum[first_root], self.minimum[second_root])
        self.components -= 1
        return True


class Solution:
    def earliestAcq(self, logs: list[list[int]], n: int) -> int:
        groups = DisjointSet(n)
        ordered = sorted(logs, key=lambda entry: entry[0])
        for timestamp, first, second in ordered:
            groups.union(first, second)
            if groups.components == 1:
                return timestamp
        return -1
