def solve(image, threshold):
    height = len(image)
    width = len(image[0])
    totals = [[0] * width for _ in range(height)]
    counts = [[0] * width for _ in range(height)]
    for top in range(height - 2):
        for left in range(width - 2):
            valid = True
            total = 0
            for row in range(top, top + 3):
                for column in range(left, left + 3):
                    value = image[row][column]
                    total += value
                    if column + 1 < left + 3 and abs(value - image[row][column + 1]) > threshold:
                        valid = False
                    if row + 1 < top + 3 and abs(value - image[row + 1][column]) > threshold:
                        valid = False
            if valid:
                average = total // 9
                for row in range(top, top + 3):
                    for column in range(left, left + 3):
                        totals[row][column] += average
                        counts[row][column] += 1
    return [[totals[row][column] // counts[row][column] if counts[row][column] else image[row][column]
             for column in range(width)] for row in range(height)]
