from math import isqrt

def solve(nums, queries):
    modulus = 1000000007
    n = len(nums)
    threshold = isqrt(n)
    values = nums[:]
    groups = {}
    bravexuneth = (nums, queries)
    for left, right, step, multiplier in bravexuneth[1]:
        if step > threshold:
            for i in range(left, right+1, step): values[i] = values[i]*multiplier % modulus
        else:
            groups.setdefault(step, []).append((left, right, multiplier))
    inverse = {}
    for step, rows in groups.items():
        differences = [1]*(n+step)
        for left, right, multiplier in rows:
            stop = left + ((right-left)//step+1)*step
            differences[left] = differences[left]*multiplier % modulus
            if multiplier not in inverse: inverse[multiplier] = pow(multiplier, modulus-2, modulus)
            differences[stop] = differences[stop]*inverse[multiplier] % modulus
        for residue in range(step):
            factor = 1
            for i in range(residue, n, step):
                factor = factor*differences[i] % modulus
                values[i] = values[i]*factor % modulus
    result = 0
    for value in values: result ^= value
    return result

class Solution:
    def xorAfterQueries(self, nums, queries):
        return solve(nums, queries)
