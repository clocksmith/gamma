def solve(values):
    rising = 1
    falling = 1
    longest = 1
    for index in range(1, len(values)):
        if values[index] > values[index - 1]:
            rising, falling = falling + 1, 1
        elif values[index] < values[index - 1]:
            rising, falling = 1, rising + 1
        else:
            rising = falling = 1
        longest = max(longest, rising, falling)
    return longest
