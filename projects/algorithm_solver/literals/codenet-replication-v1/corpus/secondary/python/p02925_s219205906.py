import sys

read = sys.stdin.read
readline = sys.stdin.readline
readlines = sys.stdin.readlines
sys.setrecursionlimit(10 ** 9)
INF = 1 << 60
MOD = 1000000007


def main():
    N = int(readline())
    A = [[int(s) - 1 for s in reversed(readline().split())] for _ in range(N)]

    M = N * (N - 1) // 2
    games = 0
    players = set(range(N))

    for d in range(1, M + 1):
        players, players_prev = set(), players
        for i in players_prev:
            if not A[i] or i in players:
                continue
            j = A[i][-1]
            if j not in players and i == A[j][-1]:
                players.add(i)
                players.add(j)
                A[i].pop()
                A[j].pop()
                games += 1

        if games == M:
            print(d)
            break

        if not players:
            print(-1)
            break

    return


if __name__ == '__main__':
    main()
