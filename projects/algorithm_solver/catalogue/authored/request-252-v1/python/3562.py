def solve(n, present, future, hierarchy, budget):
    children = [[] for _ in range(n)]
    for boss, employee in hierarchy:
        children[boss - 1].append(employee - 1)
    order = [0]
    for u in order:
        order.extend(children[u])
    impossible = float('-inf')
    dp = [None] * n

    def merge(left, right):
        result = [impossible] * (budget + 1)
        for a, profit_a in enumerate(left):
            if profit_a == impossible:
                continue
            for b in range(budget - a + 1):
                if right[b] != impossible:
                    result[a + b] = max(result[a + b], profit_a + right[b])
        return result

    for u in reversed(order):
        skip = [0] + [impossible] * budget
        buy = skip[:]
        for v in children[u]:
            skip = merge(skip, dp[v][0])
            buy = merge(buy, dp[v][1])
        states = []
        for parent_bought in (False, True):
            cost = present[u] // 2 if parent_bought else present[u]
            result = skip[:]
            for spent in range(cost, budget + 1):
                result[spent] = max(result[spent], buy[spent - cost] + future[u] - cost)
            states.append(result)
        dp[u] = states
    return max(dp[0][0])
