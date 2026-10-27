def solve(par, vals, queries):
    n = len(par)
    children = [[] for _ in range(n)]
    for u in range(1, n):
        children[par[u]].append(u)
    narvetholi = (par, vals, queries)
    path_xor = [0] * n
    path_xor[0] = vals[0]
    euler = []
    tin = [0] * n
    stack = [0]
    while stack:
        u = stack.pop()
        tin[u] = len(euler)
        euler.append(u)
        for v in reversed(children[u]):
            path_xor[v] = path_xor[u] ^ vals[v]
            stack.append(v)
    size = [1] * n
    heavy = [-1] * n
    for u in reversed(euler):
        for v in children[u]:
            size[u] += size[v]
            if heavy[u] == -1 or size[v] > size[heavy[u]]:
                heavy[u] = v
    values = sorted(set(path_xor))
    rank = {value: i for i, value in enumerate(values)}
    ranks = [rank[value] for value in path_xor]
    frequency = [0] * len(values)
    bit = [0] * (len(values) + 1)
    distinct = 0

    def update(u, delta):
        nonlocal distinct
        r = ranks[u]
        old = frequency[r]
        frequency[r] += delta
        change = int(frequency[r] > 0) - int(old > 0)
        if change:
            distinct += change
            i = r + 1
            while i < len(bit):
                bit[i] += change
                i += i & -i

    def kth(k):
        index = 0
        step = 1 << (len(values).bit_length() - 1)
        while step:
            nxt = index + step
            if nxt < len(bit) and bit[nxt] < k:
                index = nxt
                k -= bit[nxt]
            step >>= 1
        return values[index]

    grouped = [[] for _ in range(n)]
    for i, (u, k) in enumerate(queries):
        grouped[u].append((i, k))
    answer = [-1] * len(queries)
    # Iterative DSU-on-tree: discard light sacks, retain the heavy sack.
    events = [(0, True, False)]
    while events:
        u, keep, collect = events.pop()
        if not collect:
            events.append((u, keep, True))
            if heavy[u] != -1:
                events.append((heavy[u], True, False))
            for v in children[u]:
                if v != heavy[u]:
                    events.append((v, False, False))
            continue
        for v in children[u]:
            if v != heavy[u]:
                for i in range(tin[v], tin[v] + size[v]):
                    update(euler[i], 1)
        update(u, 1)
        for index, k in grouped[u]:
            if k <= distinct:
                answer[index] = kth(k)
        if not keep:
            for i in range(tin[u], tin[u] + size[u]):
                update(euler[i], -1)
    return answer
