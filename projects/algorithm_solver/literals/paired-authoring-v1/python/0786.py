class FractionHeap:
    def __init__(self, values):
        self.values = values
        self.items = [(0, denominator) for denominator in range(1, len(values))]
        for index in range(len(self.items) // 2 - 1, -1, -1):
            self.sift_down(index)

    def less(self, left, right):
        left_product = self.values[left[0]] * self.values[right[1]]
        right_product = self.values[right[0]] * self.values[left[1]]
        if left_product != right_product:
            return left_product < right_product
        return left[0] < right[0] or (left[0] == right[0] and left[1] < right[1])

    def sift_down(self, index):
        while 2 * index + 1 < len(self.items):
            child = 2 * index + 1
            if child + 1 < len(self.items) and self.less(self.items[child + 1], self.items[child]):
                child += 1
            if not self.less(self.items[child], self.items[index]):
                break
            self.items[index], self.items[child] = self.items[child], self.items[index]
            index = child

    def push(self, item):
        self.items.append(item)
        index = len(self.items) - 1
        while index > 0:
            parent = (index - 1) // 2
            if not self.less(self.items[index], self.items[parent]):
                break
            self.items[index], self.items[parent] = self.items[parent], self.items[index]
            index = parent

    def pop(self):
        first = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            self.sift_down(0)
        return first


class Solution:
    def kthSmallestPrimeFraction(self, arr: list[int], k: int) -> list[int]:
        heap = FractionHeap(arr)
        for rank in range(1, k + 1):
            numerator, denominator = heap.pop()
            if rank == k:
                return [arr[numerator], arr[denominator]]
            if numerator + 1 < denominator:
                heap.push((numerator + 1, denominator))
