def solve(root):
    if root is None:
        return ""
    nodes = [root]
    parents = [-1]
    depths = [1]
    index = 0
    while index < len(nodes):
        node = nodes[index]
        for child in (node.left, node.right):
            if child is not None:
                nodes.append(child)
                parents.append(index)
                depths.append(depths[index] + 1)
        index += 1
    ranks = [node.val for node in nodes]
    ancestors = parents[:]
    span = 1
    rank_count = 26

    def counting_order(order, keys, count):
        positions = [0] * count
        for item in order:
            positions[keys[item]] += 1
        total = 0
        for key in range(count):
            frequency = positions[key]
            positions[key] = total
            total += frequency
        result = [0] * len(order)
        for item in order:
            key = keys[item]
            result[positions[key]] = item
            positions[key] += 1
        return result

    while span < max(depths):
        suffix_ranks = [0 if ancestor < 0 else ranks[ancestor] + 1 for ancestor in ancestors]
        order = counting_order(range(len(nodes)), suffix_ranks, rank_count + 1)
        order = counting_order(order, ranks, rank_count)
        new_ranks = [0] * len(nodes)
        distinct = 1
        for position in range(1, len(order)):
            previous, current = order[position - 1], order[position]
            if ranks[previous] != ranks[current] or suffix_ranks[previous] != suffix_ranks[current]:
                distinct += 1
            new_ranks[current] = distinct - 1
        ranks = new_ranks
        ancestors = [-1 if parent < 0 else ancestors[parent] for parent in ancestors]
        rank_count = distinct
        span *= 2
    best = None
    for index, node in enumerate(nodes):
        if node.left is None and node.right is None:
            if best is None or ranks[index] < ranks[best]:
                best = index
    characters = []
    while best >= 0:
        characters.append(chr(97 + nodes[best].val))
        best = parents[best]
    return "".join(characters)
