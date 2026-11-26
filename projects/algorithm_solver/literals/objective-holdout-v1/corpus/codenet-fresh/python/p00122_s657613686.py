import sys

def generate_frog_positions(x, y):
    positions = [(x - 1, y - 2), (x, y - 2), (x + 1, y - 2),
                 (x + 2, y - 1), (x + 2, y), (x + 2, y + 1),
                 (x - 1, y + 2), (x, y + 2), (x + 1, y + 2),
                 (x - 2, y - 1), (x - 2, y), (x - 2, y + 1)]
    return [(a, b) for (a, b) in positions if 0 <= a <= 9 and 0 <= b <= 9]

def is_near_sprinkler(frog, sprinkler):
    dx = frog[0] - sprinkler[0]
    dy = frog[1] - sprinkler[1]
    return -1 <= dx <= 1 and -1 <= dy <= 1

while True:
    frog_pos = tuple([int(i) for i in sys.stdin.readline().split()])
    if frog_pos == (0, 0):
        break
    num_sprinklers = int(sys.stdin.readline())
    tmp = [int(i) for i in sys.stdin.readline().split()]
    sprinklers = zip(tmp[::2], tmp[1::2])

    positions = [frog_pos]
    for sprinkler in sprinklers:
        next_positions = []
        for pos in positions:
            next_positions += generate_frog_positions(pos[0], pos[1])
            next_positions = [pos for pos in next_positions if is_near_sprinkler(pos, sprinkler)]
        positions = next_positions
    if positions:
        print("OK")
    else:
        print("NA")