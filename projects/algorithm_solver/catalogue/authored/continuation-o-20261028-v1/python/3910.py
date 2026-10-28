"""Original frontend 3910 variant; qualification unknown."""

def solve(nums, edges):
    n = len(nums)
    adjacency = [0] * n
    for a, b in edges:
        adjacency[a] |= 1 << b
        adjacency[b] |= 1 << a
    parity = [0] * (1 << n)
    answer = 0
    for mask in range(1, 1 << n):
        bit = mask & -mask
        parity[mask] = parity[mask ^ bit] ^ nums[bit.bit_length() - 1]
        if parity[mask]:
            continue
        reached = frontier = bit
        while frontier:
            following = 0
            while frontier:
                current = frontier & -frontier
                frontier ^= current
                following |= adjacency[current.bit_length() - 1]
            frontier = following & mask & ~reached
            reached |= frontier
        answer += reached == mask
    return answer


class Solution:
    def evenSumSubgraphs(self, nums, edges):
        return solve(nums, edges)
