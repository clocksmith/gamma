def solve(nums, k):
    target = []
    for p in (2, 3, 5):
        power = 0
        while k % p == 0:
            power += 1
            k //= p
        target.append(power)
    if k != 1:
        return 0
    vectors = [(0, 0, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0), (2, 0, 0), (0, 0, 1), (1, 1, 0)]
    def half(values):
        states = {(0, 0, 0): 1}
        for x in values:
            delta = vectors[x]
            following = {}
            for state, count in states.items():
                for sign in (-1, 0, 1):
                    key = tuple(state[i] + sign * delta[i] for i in range(3))
                    following[key] = following.get(key, 0) + count
            states = following
        return states
    middle = len(nums) // 2
    left, right = half(nums[:middle]), half(nums[middle:])
    return sum(count * right.get(tuple(target[i] - state[i] for i in range(3)), 0) for state, count in left.items())


class Solution:
    def countSequences(self, nums, k):
        return solve(nums, k)
