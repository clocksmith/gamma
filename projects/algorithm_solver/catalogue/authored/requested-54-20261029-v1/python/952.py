"""Original development candidate; independent qualification pending."""
def solve(nums):
    n = len(nums)
    parent = list(range(n))
    size = [1]*n
    owners = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i,value in enumerate(nums):
        factors = []
        p = 2
        while p*p <= value:
            if value%p == 0:
                factors.append(p)
                while value%p == 0:
                    value //= p
            p += 1
        if value > 1:
            factors.append(value)
        for factor in factors:
            if factor not in owners:
                owners[factor] = i
            else:
                a,b = find(i),find(owners[factor])
                if a != b:
                    if size[a] < size[b]:
                        a,b = b,a
                    parent[b] = a
                    size[a] += size[b]
    return max(size[find(i)] for i in range(n))


class Solution:
    def largestComponentSize(self, nums):
        return solve(nums)
