"""1442. Count Triplets That Can Form Two Arrays of Equal XOR (Medium).

Specification: https://leetcode.com/problems/count-triplets-that-can-form-two-arrays-of-equal-xor/description/
"""


def solve(arr):
    prefix = [0]
    for value in arr:
        prefix.append(prefix[-1] ^ value)
    count = 0
    for i in range(len(prefix)):
        for q in range(i + 2, len(prefix)):
            if prefix[i] == prefix[q]:
                count += q - i - 1
    return count


class Solution:
    def countTriplets(self, arr):
        return solve(arr)
