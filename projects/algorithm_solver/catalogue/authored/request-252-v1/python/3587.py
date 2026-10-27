def solve(nums):
    even_positions = [i for i, value in enumerate(nums) if value % 2 == 0]
    even_count, n = len(even_positions), len(nums)
    if abs(2 * even_count - n) > 1:
        return -1
    costs = []
    for start in (0, 1):
        if len(range(start, n, 2)) == even_count:
            costs.append(sum(abs(position - (start + 2 * i))
                             for i, position in enumerate(even_positions)))
    return min(costs)
