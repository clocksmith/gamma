def solve(values, change):
    return max(0, max(values) - min(values) - 2 * change)
