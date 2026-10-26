"""1569. Number of Ways to Reorder Array to Get Same BST: iterative BST construction and subtree interleavings; O(n^2) time and O(n) space; exact modular products."""


def solve(nums: list[int]) -> int:
    modulus = 1_000_000_007
    size = len(nums)
    left = [-1] * size
    right = [-1] * size
    for index in range(1, size):
        node = 0
        while True:
            children = left if nums[index] < nums[node] else right
            if children[node] == -1:
                children[node] = index
                break
            node = children[node]
    factorial = [1] * (size + 1)
    for index in range(1, size + 1):
        factorial[index] = factorial[index - 1] * index % modulus
    inverse = [1] * (size + 1)
    inverse[size] = pow(factorial[size], modulus - 2, modulus)
    for index in range(size, 0, -1):
        inverse[index - 1] = inverse[index] * index % modulus
    counts = [0] * size
    ways = [1] * size
    # Every child was inserted after its parent: reverse insertion order is postorder-compatible.
    for node in range(size - 1, -1, -1):
        left_size = counts[left[node]] if left[node] != -1 else 0
        right_size = counts[right[node]] if right[node] != -1 else 0
        interleavings = factorial[left_size + right_size] * inverse[left_size] % modulus * inverse[right_size] % modulus
        if left[node] != -1:
            interleavings = interleavings * ways[left[node]] % modulus
        if right[node] != -1:
            interleavings = interleavings * ways[right[node]] % modulus
        counts[node] = left_size + right_size + 1
        ways[node] = interleavings
    return (ways[0] - 1) % modulus


class Solution:
    def numOfWays(self, nums: list[int]) -> int:
        return solve(nums)
