import itertools


def check(x: int) -> bool:
    s = str(x)
    prev = ord(s[0])
    for c in s[1:]:
        if ord(c) != prev+1:
            return False
        prev = ord(c)
    return True


def main() -> None:
    n = int(input())
    v = list(map(int, input().split(' ')))
    max_ = -1
    for c in itertools.combinations(sorted(v), 2):
        p = c[0] * c[1]
        if check(p):
            max_ = max(max_, p)

    print(max_)


if __name__ == '__main__':
    main()
