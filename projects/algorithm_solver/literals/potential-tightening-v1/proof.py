"""Small supplied-DAG theorem oracle; no corpus loader or production runner."""


def suffix(length, edges, denominator):
    """Edges are (start, end, multiplier); all suffixes must be reachable."""
    assert type(denominator) is int and denominator > 0
    rows = [[] for _ in range(length)]
    for start, end, q in edges:
        assert 0 <= start < end <= length and type(q) is int and q >= 0
        rows[start].append((end, q))
    distance = [None] * length + [0]
    for start in range(length - 1, -1, -1):
        assert rows[start]
        distance[start] = min((9 if end - start == 1 else -1) * denominator
                              + q + distance[end] for end, q in rows[start])
    return distance


def tight_multiplier(distance, start, end, denominator):
    base = 9 if end - start == 1 else -1
    return max(0, distance[start] - distance[end] - base * denominator)


def lift(length, old_edges, full_edges, denominator, *, tighten_old):
    """Retain old penalties (50) or remove their slack (53)."""
    distance = suffix(length, old_edges, denominator)
    old = {(start, end): q for start, end, q in old_edges}
    assert len(old) == len(old_edges) and set(old) <= set(full_edges)
    result = []
    for start, end in full_edges:
        minimum = tight_multiplier(distance, start, end, denominator)
        if (start, end) in old:
            assert minimum <= old[start, end]
        q = minimum if tighten_old or (start, end) not in old else old[start, end]
        result.append((start, end, q))
    assert suffix(length, result, denominator) == distance
    return distance, result
