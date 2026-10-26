"""2935. Maximum Strong Pair XOR II.

Sorted sliding window and a counted binary trie; O(n log n + n*B) time, O(n*B) space. Inputs are preserved.
"""

def solve(nums: list[int]) -> int:
    values = sorted(nums)
    bits = max(1, max(values).bit_length())
    children, counts = [[-1, -1]], [0]

    def update(value, change):
        state = 0
        counts[state] += change
        for bit in range(bits - 1, -1, -1):
            digit = value >> bit & 1
            if children[state][digit] == -1:
                children[state][digit] = len(children)
                children.append([-1, -1])
                counts.append(0)
            state = children[state][digit]
            counts[state] += change

    left = answer = 0
    for value in values:
        update(value, 1)
        while value > 2 * values[left]:
            update(values[left], -1)
            left += 1
        state = score = 0
        for bit in range(bits - 1, -1, -1):
            digit = value >> bit & 1
            opposite = children[state][digit ^ 1]
            if opposite != -1 and counts[opposite]:
                score |= 1 << bit
                state = opposite
            else:
                state = children[state][digit]
        answer = max(answer, score)
    return answer


class Solution:
    def maximumStrongPairXor(self, nums: list[int]) -> int:
        return solve(nums)
