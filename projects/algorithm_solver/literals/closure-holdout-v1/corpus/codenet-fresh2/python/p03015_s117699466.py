import sys
sys.setrecursionlimit(10 ** 7)

read = sys.stdin.buffer.read
readline = sys.stdin.buffer.readline
readlines = sys.stdin.buffer.readlines

L = input()
N = len(L)
MOD = 10 ** 9 + 7

ans = 0

# one cnt
cnt = 0
for i in range(N):
    if L[i] == '1':
        cnt += 1
        ans += pow(3, N - i - 1, MOD) * pow(2, cnt - 1, MOD)
        ans %= MOD

ans += pow(2, cnt, MOD)
ans %= MOD

print(ans)
