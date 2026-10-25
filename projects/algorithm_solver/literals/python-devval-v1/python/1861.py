def solve(box):
    height = len(box)
    width = len(box[0])
    result = [["."] * height for _ in range(width)]
    for row in range(height):
        destination = width - 1
        for column in range(width - 1, -1, -1):
            if box[row][column] == "*":
                result[column][height - 1 - row] = "*"
                destination = column - 1
            elif box[row][column] == "#":
                result[destination][height - 1 - row] = "#"
                destination -= 1
    return result
