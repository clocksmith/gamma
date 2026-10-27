def solve(nums, k):
    n = len(nums)
    prefix = [0]
    for value in nums:
        prefix.append(prefix[-1] ^ value)
    previous = [float('inf')] * (n + 1)
    previous[0] = 0
    for parts in range(1, k + 1):
        current = [float('inf')] * (n + 1)
        for end in range(parts, n + 1):
            current[end] = min(max(previous[start], prefix[end] ^ prefix[start])
                               for start in range(parts - 1, end))
        previous = current
    return previous[n]
