def solve(nums, k):
    for target in (1, -1):
        previous_flip = 1
        operations = 0
        for i in range(len(nums) - 1):
            if nums[i] * previous_flip != target:
                operations += 1
                previous_flip = -1
            else:
                previous_flip = 1
        if nums[-1] * previous_flip == target and operations <= k:
            return True
    return False
