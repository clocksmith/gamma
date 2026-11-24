#!/usr/bin/env python3


def solve(n, m, a, b, ds):
    is_waste = [False for _ in range(n)]
    for i in range(n):
        if ds[i] >= a:
            is_waste[i] = True
        else:
            break
    if sum(is_waste) > n - m:
        for i in range(n)[::-1]:
            if is_waste[i]:
                if ds[i] <= b:
                    is_waste[i] = False
                else:
                    break
    return sum(is_waste)


def main():
    n, m, a, b = map(int, input().split())
    ds = list(map(int, input().split()))
    print(solve(n, m, a, b, ds))


if __name__ == '__main__':
    main()