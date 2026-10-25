def solve(nums: list[int]) -> int:
    """Enumerate distinct index pairs. O(n^2 log M) time, O(1) space."""
    def gcd(left: int, right: int) -> int:
        while right:
            left, right = right, left % right
        return left

    answer = 0
    for left in range(len(nums)):
        for right in range(left + 1, len(nums)):
            divisor = gcd(nums[left], nums[right])
            strength = (nums[left] // divisor) * (nums[right] // divisor)
            answer = max(answer, strength)
    return answer
