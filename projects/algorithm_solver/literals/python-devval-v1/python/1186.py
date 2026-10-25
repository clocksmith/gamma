def solve(values):
    without_deletion = values[0]
    with_deletion = None
    best = values[0]
    for value in values[1:]:
        if with_deletion is None:
            new_with_deletion = without_deletion
        else:
            new_with_deletion = max(without_deletion, with_deletion + value)
        without_deletion = max(value, without_deletion + value)
        with_deletion = new_with_deletion
        best = max(best, without_deletion, with_deletion)
    return best
