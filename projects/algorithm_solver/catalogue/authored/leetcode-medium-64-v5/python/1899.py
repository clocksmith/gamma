"""1899. Merge Triplets to Form Target Triplet: collect target coordinates only from triplets that cannot overshoot."""


def solve(triplets: list[list[int]], target: list[int]) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    found = [False] * 3
    for triplet in triplets:
        if any(triplet[index] > target[index] for index in range(3)):
            continue
        for index in range(3):
            if triplet[index] == target[index]:
                found[index] = True
        if all(found):
            return True
    return False


class Solution:
    def mergeTriplets(self, triplets: list[list[int]], target: list[int]) -> bool:
        return solve(triplets, target)
