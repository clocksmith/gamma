def solve(moves):
    horizontal = 0
    vertical = 0
    for move in moves:
        if move == "U":
            vertical += 1
        elif move == "D":
            vertical -= 1
        elif move == "L":
            horizontal -= 1
        else:
            horizontal += 1
    return horizontal == 0 and vertical == 0
