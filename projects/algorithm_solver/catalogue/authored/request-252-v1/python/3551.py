def solve(nums):
    order = sorted(range(len(nums)), key=lambda i: (sum(map(int, str(nums[i]))), nums[i]))
    seen = [False] * len(nums)
    answer = 0
    for start in range(len(nums)):
        length, current = 0, start
        while not seen[current]:
            seen[current] = True
            length += 1
            current = order[current]
        if length:
            answer += length - 1
    return answer
