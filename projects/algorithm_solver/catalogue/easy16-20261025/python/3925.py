def solve(nums: list[int]) -> list[int]:
    """Return the input followed by its reverse. O(n) time and output space."""
    length = len(nums)
    answer = [0] * (2 * length)
    for index in range(length):
        answer[index] = nums[index]
        answer[length + index] = nums[length - index - 1]
    return answer
