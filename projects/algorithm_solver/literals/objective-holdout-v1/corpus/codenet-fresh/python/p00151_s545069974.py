def scanning_area(grid, length, point_list, stride_x, stride_y):
    area = [[0 for _ in range(length + 1)] for __ in range(length + 1)]
    max_length = 0

    for row, col in point_list:
        if grid[row][col] == "1":
            area[row + stride_y][col + stride_x] = area[row][col] + 1
            max_length = max(max_length, area[row + stride_y][col + stride_x])

    return max_length


def create_point_list(length):
    points = []

    for count, r in enumerate(range(length - 1, 0, -1), 1):
        row = r
        for col in range(0, count, 1):
            points.append((row, col))
            row += 1

    for index in range(0, length):
        points.append((index, index))

    for lp in range(1, length):
        row = 0
        for col in range(lp, length):
            points.append((row, col))
            row += 1

    return points


while True:

    length = int(input())

    if length == 0:
        break

    grid = [input() for _ in range(length)]

    point_list = [[row, col] for row in range(length) for col in range(length)]

    line_length1 = scanning_area(grid, length, point_list, 1, 0)
    line_length2 = scanning_area(grid, length, point_list, 0, 1)

    point_list = create_point_list(length)
    line_length3 = scanning_area(grid, length, point_list, 1, 1)
    point_list.reverse()
    line_length4 = scanning_area(grid, length, point_list, -1, 1)

    max_length = max(line_length1, line_length2, line_length3, line_length4)
    print(max_length)

