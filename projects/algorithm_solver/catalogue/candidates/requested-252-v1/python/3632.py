"""3632. Subarrays with XOR at Least K.

Specification: https://leetcode.com/problems/subarrays-with-xor-at-least-k/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n * bitWidth) time and space; unsigned nonnegative 32-bit input domain.
Inputs are not modified.
Exact Gamma input bounds and method signature require coordinator reconciliation.
"""

def solve(nums, k):
    maximum = max(max(nums, default=0), k)
    width = max(1, maximum.bit_length())
    children = [[-1, -1]]
    counts = [0]
    def insert(value):
        node = 0
        counts[node] += 1
        for bit in range(width - 1, -1, -1):
            direction = (value >> bit) & 1
            target = children[node][direction]
            if target == -1:
                target = len(children)
                children[node][direction] = target
                children.append([-1, -1])
                counts.append(0)
            node = target
            counts[node] += 1
    def less_than(value):
        node = 0
        total = 0
        for bit in range(width - 1, -1, -1):
            if node == -1:
                break
            direction = (value >> bit) & 1
            if (k >> bit) & 1:
                same = children[node][direction]
                if same != -1:
                    total += counts[same]
                node = children[node][direction ^ 1]
            else:
                node = children[node][direction]
        return total
    insert(0)
    prefix = answer = 0
    for index, value in enumerate(nums):
        prefix ^= value
        answer += index + 1 - less_than(prefix)
        insert(prefix)
    return answer


class Solution:
    def countSubarrays(self, nums, k):
        return solve(nums, k)
