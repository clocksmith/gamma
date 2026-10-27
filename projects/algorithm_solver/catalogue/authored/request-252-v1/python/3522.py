def solve(instructions, values):
    seen = bytearray(len(values))
    index = score = 0
    while 0 <= index < len(values) and not seen[index]:
        seen[index] = 1
        if instructions[index] == 'add':
            score += values[index]
            index += 1
        else:
            index += values[index]
    return score
