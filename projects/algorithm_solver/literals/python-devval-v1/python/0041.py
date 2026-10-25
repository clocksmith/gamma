def solve(values):
    length = len(values)
    for index in range(length):
        while 1 <= values[index] <= length:
            destination = values[index] - 1
            if values[destination] == values[index]:
                break
            values[index], values[destination] = values[destination], values[index]
    for index, value in enumerate(values):
        if value != index + 1:
            return index + 1
    return length + 1
