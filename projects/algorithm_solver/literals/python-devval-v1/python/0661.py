def solve(image):
    height = len(image)
    width = len(image[0])
    result = []
    for row in range(height):
        output_row = []
        for column in range(width):
            total = 0
            count = 0
            for neighbor_row in range(max(0, row - 1), min(height, row + 2)):
                for neighbor_column in range(max(0, column - 1), min(width, column + 2)):
                    total += image[neighbor_row][neighbor_column]
                    count += 1
            output_row.append(total // count)
        result.append(output_row)
    return result
