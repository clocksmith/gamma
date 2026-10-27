# Original candidate; contract and evidence: ../batch1/manifest.json
from math import prod


def solve(nums, target):
    if prod(nums) != target * target:
        return False
    def search(index, product, selected):
        if index == len(nums):
            return 0 < selected < len(nums) and product == target
        if search(index + 1, product, selected):
            return True
        next_product = product * nums[index]
        return (next_product <= target and target % next_product == 0
                and search(index + 1, next_product, selected + 1))
    return search(0, 1, 0)
