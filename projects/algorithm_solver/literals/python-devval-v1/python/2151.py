def solve(statements):
    count = len(statements)
    required_good = [0] * count
    required_bad = [0] * count
    for speaker in range(count):
        for person in range(count):
            if statements[speaker][person] == 1:
                required_good[speaker] |= 1 << person
            elif statements[speaker][person] == 0:
                required_bad[speaker] |= 1 << person
    maximum = 0
    for mask in range(1 << count):
        valid = True
        for speaker in range(count):
            if mask & (1 << speaker):
                if mask & required_bad[speaker] or required_good[speaker] & ~mask:
                    valid = False
                    break
        if valid:
            maximum = max(maximum, mask.bit_count())
    return maximum
