def solve(label):
    first = 1 << (label.bit_length() - 1)
    path = []
    while first:
        path.append(label)
        label = (3 * first - 1 - label) // 2
        first //= 2
    path.reverse()
    return path
