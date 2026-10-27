def solve(nums, k, queries):
    """Segment monoid: total product and counts of nonempty prefix products."""
    n = len(nums)
    size = 1
    while size < n:
        size *= 2
    identity = (1 % k, [0] * k)
    tree = [identity for _ in range(2 * size)]

    def merge(left, right):
        product, counts = left[0], left[1].copy()
        for remainder, count in enumerate(right[1]):
            counts[product * remainder % k] += count
        return product * right[0] % k, counts

    def leaf(value):
        counts = [0] * k
        counts[value % k] = 1
        return value % k, counts

    for i, value in enumerate(nums):
        tree[size + i] = leaf(value)
    for node in range(size - 1, 0, -1):
        tree[node] = merge(tree[2 * node], tree[2 * node + 1])
    answers = []
    for index, value, start, x in queries:
        node = size + index
        tree[node] = leaf(value)
        node //= 2
        while node:
            tree[node] = merge(tree[2 * node], tree[2 * node + 1])
            node //= 2
        low, high = size + start, size + n
        left = right = identity
        while low < high:
            if low % 2:
                left = merge(left, tree[low])
                low += 1
            if high % 2:
                high -= 1
                right = merge(tree[high], right)
            low //= 2
            high //= 2
        answers.append(merge(left, right)[1][x])
    return answers
