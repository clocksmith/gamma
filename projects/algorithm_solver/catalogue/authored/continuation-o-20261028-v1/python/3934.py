"""Original frontend 3934 variant; qualification unknown."""

def solve(nums):
    n = len(nums)
    ranks_by_value = {value: i for i, value in enumerate(sorted(set(nums)))}
    rank = [ranks_by_value[value] for value in nums]
    classes = len(ranks_by_value)
    suffixes = sorted(range(n), key=rank.__getitem__)
    width = 1
    def counting(items, offset):
        counts = [0] * (classes + 1)
        for index in items:
            key = rank[index + offset] + 1 if index + offset < n else 0
            counts[key] += 1
        position = 0
        for i, count in enumerate(counts):
            counts[i], position = position, position + count
        result = [0] * n
        for index in items:
            key = rank[index + offset] + 1 if index + offset < n else 0
            result[counts[key]] = index
            counts[key] += 1
        return result
    while classes < n:
        suffixes = counting(counting(suffixes, width), 0)
        following = [0] * n
        new_classes = 1
        for j in range(1, n):
            a, b = suffixes[j - 1], suffixes[j]
            if rank[a] != rank[b] or (rank[a + width] if a + width < n else -1) != (rank[b + width] if b + width < n else -1):
                new_classes += 1
            following[b] = new_classes - 1
        rank, classes = following, new_classes
        width *= 2
    inverse = [0] * n
    for i, index in enumerate(suffixes):
        inverse[index] = i
    lcp = [0] * n
    matched = 0
    for index in range(n):
        position = inverse[index]
        if position == 0:
            matched = 0
            continue
        other = suffixes[position - 1]
        while index + matched < n and other + matched < n and nums[index + matched] == nums[other + matched]:
            matched += 1
        lcp[position] = matched
        matched = max(0, matched - 1)
    answer = n
    for position, index in enumerate(suffixes):
        required = max(lcp[position], lcp[position + 1] if position + 1 < n else 0) + 1
        if required <= n - index:
            answer = min(answer, required)
    return answer


class Solution:
    def smallestUniqueSubarray(self, nums):
        return solve(nums)
