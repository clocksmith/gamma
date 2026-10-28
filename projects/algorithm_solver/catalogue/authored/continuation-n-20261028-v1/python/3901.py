"""Original frontend 3901 variant; qualification unknown."""

def solve(nums, p, queries):
    from math import gcd
    values = nums[:]
    n = len(values)
    size = 1
    while size < n:
        size *= 2
    tree = [0] * (size * 2)
    eligible = 0
    for i, value in enumerate(values):
        if value % p == 0:
            tree[size + i] = value
            eligible += 1
    for node in range(size - 1, 0, -1):
        tree[node] = gcd(tree[node * 2], tree[node * 2 + 1])
    answer = 0
    for index, value in queries:
        eligible += int(value % p == 0) - int(values[index] % p == 0)
        values[index] = value
        node = size + index
        tree[node] = value if value % p == 0 else 0
        node //= 2
        while node:
            tree[node] = gcd(tree[node * 2], tree[node * 2 + 1])
            node //= 2
        good = tree[1] == p
        if good and eligible == n and n <= 16:
            prefix = [0]
            for current in values:
                prefix.append(gcd(prefix[-1], current))
            suffix = 0
            good = False
            for i in range(n - 1, -1, -1):
                if gcd(prefix[i], suffix) == p:
                    good = True
                    break
                suffix = gcd(suffix, values[i])
        answer += good
    return answer


class Solution:
    def countGoodSubseq(self, nums, p, queries):
        return solve(nums, p, queries)
