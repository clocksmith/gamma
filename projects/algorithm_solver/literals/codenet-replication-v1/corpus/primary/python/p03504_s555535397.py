n,c = map(int,input().split())
ab = []
for _ in range(n):
    s, t, cha = (int(x) for x in input().split())
    ab.append([s, t, cha])

ab = sorted(ab, key=lambda x: x[0])
ab = sorted(ab, key=lambda x: x[2])

for i in range(1,n):
    if ab[i][0] == ab[i-1][1] and ab[i][2] == ab[i-1][2]:
        ab[i][0] = ab[i-1][0]
        ab[i-1][0] = -1

time = [0]*(10**5+1)

for i in range(n):
    if ab[i][0] == -1:
        continue
    time[ab[i][0]-1] += 1
    time[ab[i][1]] -= 1

ans = 0
memo = 0

for i in time:
    memo += i
    ans = max(ans,memo)

print(ans)