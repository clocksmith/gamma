"""2440. Create Components With Same Value. Try divisor component sums and greedily close subtrees in postorder."""


def solve(nums: list[int], edges: list[list[int]]) -> int:
    """O(sqrt(S)+n*tau(S)+tau(S) log tau(S)) time and O(n+tau(S)) space, S=sum(nums). Inputs are preserved."""
    size = len(nums)
    graph = [[] for _ in nums]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = [-1] * size
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    total = sum(nums)
    largest = max(nums)
    targets = set()
    divisor = 1
    while divisor * divisor <= total:
        if total % divisor == 0:
            targets.add(divisor)
            targets.add(total // divisor)
        divisor += 1
    for target in sorted(targets):
        if target < largest or total // target > size:
            continue
        remaining = nums.copy()
        feasible = True
        for node in reversed(order):
            if remaining[node] > target:
                feasible = False
                break
            if remaining[node] == target:
                remaining[node] = 0
            if parent[node] != -1:
                remaining[parent[node]] += remaining[node]
        if feasible and remaining[0] == 0:
            return total // target - 1
    return 0


class Solution:
    def componentValue(self, nums: list[int], edges: list[list[int]]) -> int:
        return solve(nums, edges)
