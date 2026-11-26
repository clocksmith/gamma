N = int(input())
l = [list(map(int, input().split())) for _ in range(N)]

diff = [0] * 100002
for k in l :
    diff[k[0] - 1] += 1
    diff[k[1]] -= 1

hist = [0,0]
for i in range(2, N + 2) :
    hist.append(hist[-1] + diff[i-1])

print(max([0] + [y - 1 for (x,y) in zip(hist, range(N + 2)) if x + 1 >= y]))