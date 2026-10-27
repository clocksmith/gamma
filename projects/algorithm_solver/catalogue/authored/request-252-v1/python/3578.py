# Original candidate; contract and evidence: ../batch1/manifest.json
from collections import deque


def solve(nums, k):
    minimum, maximum = deque(), deque()
    prefix = [0, 1]
    left = 0
    answer = 0
    for right, value in enumerate(nums):
        while minimum and nums[minimum[-1]] >= value:
            minimum.pop()
        while maximum and nums[maximum[-1]] <= value:
            maximum.pop()
        minimum.append(right)
        maximum.append(right)
        while nums[maximum[0]] - nums[minimum[0]] > k:
            if minimum[0] == left:
                minimum.popleft()
            if maximum[0] == left:
                maximum.popleft()
            left += 1
        answer = (prefix[right + 1] - prefix[left]) % 1_000_000_007
        prefix.append((prefix[-1] + answer) % 1_000_000_007)
    return answer
