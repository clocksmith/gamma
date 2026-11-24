from sys import stdin


def main():
    n = int(stdin.readline())
    a = map(int, stdin.readline().split())
    r = [0] * 13
    for ai in a:
        r[int(ai / 400)] += 1
    min = 0
    for i in range(8):
        if r[i] > 0:
            min += 1
    max = min
    for i in range(8, 13):
        max += r[i]
    if min == 0:
        min = 1
    print(min, max)


if __name__ == "__main__":
    main()
