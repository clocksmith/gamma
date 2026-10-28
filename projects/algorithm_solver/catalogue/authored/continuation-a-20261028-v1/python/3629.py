from collections import deque
from math import isqrt

def solve(nums):
    maximum = max(nums)
    smallest = list(range(maximum + 1))
    for prime in range(2, isqrt(maximum) + 1):
        if smallest[prime] == prime:
            for value in range(prime * prime, maximum + 1, prime):
                if smallest[value] == value:
                    smallest[value] = prime
    prime_values = {value for value in nums if value >= 2 and smallest[value] == value}
    divisible = {prime: [] for prime in prime_values}
    for index, value in enumerate(nums):
        while value > 1:
            prime = smallest[value]
            if prime in divisible:
                divisible[prime].append(index)
            while value % prime == 0:
                value //= prime
    distance = [-1] * len(nums)
    distance[0] = 0
    queue = deque([0])
    while queue:
        index = queue.popleft()
        if index == len(nums) - 1:
            return distance[index]
        targets = divisible.pop(nums[index], [])
        targets.extend((index - 1, index + 1))
        for other in targets:
            if 0 <= other < len(nums) and distance[other] < 0:
                distance[other] = distance[index] + 1
                queue.append(other)
    return -1


class Solution:
    def minJumps(self, nums):
        return solve(nums)
