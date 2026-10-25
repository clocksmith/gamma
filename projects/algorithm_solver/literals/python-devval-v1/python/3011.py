def solve(values):
    previous_maximum = None
    group_maximum = None
    group_bits = None
    for value in values:
        bits = value.bit_count()
        if bits != group_bits:
            previous_maximum = group_maximum
            group_maximum = value
            group_bits = bits
        else:
            group_maximum = max(group_maximum, value)
        if previous_maximum is not None and previous_maximum > value:
            return False
    return True
