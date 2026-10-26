"""1687. Delivering Boxes from Storage to Ports: prefix weights, port changes and a monotonic DP deque; O(n) time and O(n) space."""

from collections import deque


def solve(boxes: list[list[int]], portsCount: int, maxBoxes: int, maxWeight: int) -> int:
    size = len(boxes)
    weight = [0] * (size + 1)
    changes = [0] * (size + 1)
    for count in range(1, size + 1):
        weight[count] = weight[count - 1] + boxes[count - 1][1]
        changes[count] = changes[count - 1] + int(count > 1 and boxes[count - 1][0] != boxes[count - 2][0])
    best = [0] * (size + 1)
    queue = deque([0])
    for count in range(1, size + 1):
        while count - queue[0] > maxBoxes or weight[count] - weight[queue[0]] > maxWeight:
            queue.popleft()
        previous = queue[0]
        best[count] = best[previous] + changes[count] - changes[previous + 1] + 2
        if count < size:
            value = best[count] - changes[count + 1]
            while queue and best[queue[-1]] - changes[queue[-1] + 1] >= value:
                queue.pop()
            queue.append(count)
    return best[size]


class Solution:
    def boxDelivering(self, boxes: list[list[int]], portsCount: int, maxBoxes: int, maxWeight: int) -> int:
        return solve(boxes, portsCount, maxBoxes, maxWeight)
