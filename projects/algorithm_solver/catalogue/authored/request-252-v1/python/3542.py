def solve(nums):
    stack = [0]
    operations = 0
    for value in nums:
        while stack[-1] > value:
            stack.pop()
        if stack[-1] < value:
            stack.append(value)
            operations += 1
    return operations
