"""1803. Count Pairs With XOR in a Range."""


def solve(nums: list[int], low: int, high: int) -> int:
    """Count prior XORs below each endpoint in a binary trie; O(n*B) time and O(n*B) space. Inputs are preserved."""
    width = max(max(nums, default=0), high + 1).bit_length()
    children = [[-1, -1]]
    counts = [0]

    def below(value, bound):
        if bound <= 0:
            return 0
        node = 0
        total = 0
        for bit in range(width - 1, -1, -1):
            if node < 0:
                break
            digit = (value >> bit) & 1
            if (bound >> bit) & 1:
                same = children[node][digit]
                if same >= 0:
                    total += counts[same]
                node = children[node][digit ^ 1]
            else:
                node = children[node][digit]
        return total

    answer = 0
    for value in nums:
        answer += below(value, high + 1) - below(value, low)
        node = 0
        for bit in range(width - 1, -1, -1):
            digit = (value >> bit) & 1
            if children[node][digit] < 0:
                children[node][digit] = len(children)
                children.append([-1, -1])
                counts.append(0)
            node = children[node][digit]
            counts[node] += 1
    return answer


class Solution:
    def countPairs(self, nums: list[int], low: int, high: int) -> int:
        return solve(nums, low, high)
