"""3130. Find All Possible Stable Binary Arrays II."""

def solve(zero: int, one: int, limit: int) -> int:
    """O(zero*one) time and space; subtract runs exceeding limit from two ending states."""
    modulus = 1_000_000_007
    ending_one = [[0] * (one + 1) for _ in range(zero + 1)]
    for used_one in range(1, min(one, limit) + 1):
        ending_one[0][used_one] = 1
    previous_zero = [0] * (one + 1)
    for used_zero in range(1, zero + 1):
        current_zero = [0] * (one + 1)
        current_zero[0] = int(used_zero <= limit)
        for used_one in range(1, one + 1):
            excluded = ending_one[used_zero - limit - 1][used_one] if used_zero > limit else 0
            current_zero[used_one] = (
                previous_zero[used_one] + ending_one[used_zero - 1][used_one] - excluded
            ) % modulus
            excluded = current_zero[used_one - limit - 1] if used_one > limit else 0
            ending_one[used_zero][used_one] = (
                current_zero[used_one - 1] + ending_one[used_zero][used_one - 1] - excluded
            ) % modulus
        previous_zero = current_zero
    return (previous_zero[one] + ending_one[zero][one]) % modulus


class Solution:
    def numberOfStableArrays(self, zero: int, one: int, limit: int) -> int:
        return solve(zero, one, limit)
