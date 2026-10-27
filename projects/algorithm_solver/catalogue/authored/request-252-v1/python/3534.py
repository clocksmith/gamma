def solve(n, nums, maxDiff, queries):
    order = sorted(range(n), key=nums.__getitem__)
    rank = [0] * n
    values = [nums[u] for u in order]
    for i, u in enumerate(order):
        rank[u] = i
    component = [0] * n
    farthest = [0] * n
    right = 0
    for left in range(n):
        if left and values[left] - values[left - 1] > maxDiff:
            component[left] = component[left - 1] + 1
        elif left:
            component[left] = component[left - 1]
        while right + 1 < n and values[right + 1] - values[left] <= maxDiff:
            right += 1
        farthest[left] = right
    jump = [farthest]
    for _ in range(1, n.bit_length()):
        previous = jump[-1]
        jump.append([previous[previous[i]] for i in range(n)])
    answer = []
    for u, v in queries:
        a, b = sorted((rank[u], rank[v]))
        if a == b:
            answer.append(0)
        elif component[a] != component[b]:
            answer.append(-1)
        else:
            distance = 0
            for level in range(len(jump) - 1, -1, -1):
                if jump[level][a] < b:
                    a = jump[level][a]
                    distance += 1 << level
            answer.append(distance + 1)
    return answer
