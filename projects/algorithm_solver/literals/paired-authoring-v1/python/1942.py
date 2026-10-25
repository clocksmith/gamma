class MinimumHeap:
    def __init__(self):
        self.items = []

    def push(self, value: int) -> None:
        self.items.append(value)
        index = len(self.items) - 1
        while index > 0:
            parent = (index - 1) // 2
            if self.items[parent] <= self.items[index]:
                break
            self.items[parent], self.items[index] = self.items[index], self.items[parent]
            index = parent

    def pop(self) -> int:
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
                if right < len(self.items) and self.items[right] < self.items[left]:
                    child = right
                if self.items[index] <= self.items[child]:
                    break
                self.items[index], self.items[child] = self.items[child], self.items[index]
                index = child
        return result


class Solution:
    def smallestChair(self, times: list[list[int]], targetFriend: int) -> int:
        events = []
        for friend, (arrival, departure) in enumerate(times):
            events.append((arrival, 1, friend))
            events.append((departure, 0, friend))
        events.sort()
        assigned = [-1] * len(times)
        available = MinimumHeap()
        next_chair = 0
        for _, kind, friend in events:
            if kind == 0:
                available.push(assigned[friend])
            else:
                if available.items:
                    chair = available.pop()
                else:
                    chair = next_chair
                    next_chair += 1
                assigned[friend] = chair
                if friend == targetFriend:
                    return chair
        return -1
