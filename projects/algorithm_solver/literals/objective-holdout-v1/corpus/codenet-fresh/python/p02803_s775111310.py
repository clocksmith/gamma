import sys
from copy import deepcopy
from itertools import combinations_with_replacement, product
from collections import deque
def input(): return sys.stdin.readline().rstrip()


def main():
    h, w = map(int, input().split())
    s = [list(input()) for i in range(h)]
    ans = 0
    for H, W in product(range(h), range(w)):
        if s[H][W] == '#':
            continue
        s2 = deepcopy(s)
        s2[H][W] = 0
        d = deque()
        d.append([H, W])
        while d:
            Hn,Wn = d.popleft()
            for i, j in [[0, 1], [1, 0], [0, -1], [-1, 0]]:
                if ((0 <= Hn+i < h) and (0 <= Wn+j < w)):
                    
                    if s2[Hn+i][Wn+j] != '.':
                        continue
                    s2[Hn+i][Wn+j] = s2[Hn][Wn] + 1
                    d.append([Hn+i, Wn+j])
                    if ans < s2[Hn+i][Wn+j]:
                        ans = s2[Hn+i][Wn+j]
        del s2

    print(ans)


if __name__ == '__main__':
    main()