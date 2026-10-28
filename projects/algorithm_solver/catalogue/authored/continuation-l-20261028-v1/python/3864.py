"""Original frontend 3864 variant; qualification unknown."""

def solve(s, encCost, flatCost):
    prefix = [0]
    for char in s:
        prefix.append(prefix[-1] + int(char == '1'))
    def cost(left, right):
        count = prefix[right] - prefix[left]
        if count == 0:
            return flatCost
        length = right - left
        own = length * count * encCost
        if length % 2:
            return own
        middle = (left + right) // 2
        return min(own, cost(left, middle) + cost(middle, right))
    return cost(0, len(s))


class Solution:
    def minCost(self, s, encCost, flatCost):
        return solve(s, encCost, flatCost)
