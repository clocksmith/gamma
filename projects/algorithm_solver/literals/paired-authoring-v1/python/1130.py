class Solution:
    def mctFromLeafValues(self, arr: list[int]) -> int:
        stack = []
        cost = 0
        for value in arr:
            while stack and stack[-1] <= value:
                middle = stack.pop()
                neighbor = min(stack[-1], value) if stack else value
                cost += middle * neighbor
            stack.append(value)
        while len(stack) > 1:
            middle = stack.pop()
            cost += middle * stack[-1]
        return cost
