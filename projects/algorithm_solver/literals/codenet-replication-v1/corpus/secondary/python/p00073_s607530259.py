import math
while 1:
    x = int(input())
    h = int(input())
    if x == h == 0:
        break

    b = math.sqrt(h * h + x * x / 4) * x / 2
    print(4 * b + x * x)

