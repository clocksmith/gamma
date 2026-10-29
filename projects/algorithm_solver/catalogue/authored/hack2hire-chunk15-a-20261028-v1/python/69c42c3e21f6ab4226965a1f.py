"""Hack2Hire 69c42c3e21f6ab4226965a1f (Copy Neighbor Sums Between Binary Trees) over an INFERRED spec; qualification unknown."""


def decode(tree):
    if not tree:
        return [], [], []
    values, left, right = [tree[0]], [-1], [-1]
    node, i = 0, 1
    while node < len(values) and i < len(tree):
        for side in (left, right):
            if i < len(tree):
                if tree[i] is not None:
                    side[node] = len(values)
                    values.append(tree[i])
                    left.append(-1)
                    right.append(-1)
                i += 1
        node += 1
    return values, left, right


def solve(trees):
    values, left, right = decode(trees[-1])
    for tree in trees[:-1]:
        sv, sl, sr = decode(tree)
        if not sv:
            continue
        if not values:
            values.append(0)
            left.append(-1)
            right.append(-1)
        pairs, head = [(0, 0)], 0
        while head < len(pairs):
            s, t = pairs[head]
            head += 1
            values[t] += sv[s] + (sv[sl[s]] if sl[s] >= 0 else 0) + (sv[sr[s]] if sr[s] >= 0 else 0)
            for source_side, target_side in ((sl, left), (sr, right)):
                child = source_side[s]
                if child >= 0:
                    if target_side[t] < 0:
                        target_side[t] = len(values)
                        values.append(0)
                        left.append(-1)
                        right.append(-1)
                    pairs.append((child, target_side[t]))
    if not values:
        return []
    out, queue, head = [values[0]], [0], 0
    while head < len(queue):
        node = queue[head]
        head += 1
        for child in (left[node], right[node]):
            if child >= 0:
                out.append(values[child])
                queue.append(child)
            else:
                out.append(None)
    while out[-1] is None:
        out.pop()
    return out


class Solution:
    def copyNeighborSums(self, trees):
        return solve(trees)
