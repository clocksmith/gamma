N = int(input())
d_list = list(map(int,input().split()))

dist = [0] * 10**5
max_d = 0
for d in d_list:
    dist[d] += 1
    max_d = max(max_d, d)

MOD = 998244353
if d_list[0] != 0:
    print(0)
    exit()
elif dist[0]>1:
    print(0)
    exit()

ans = 1
for i in range(max_d):
    if dist[i] == 0 or dist[i+1] ==0:
        print(0)
        exit()
    ans *= (dist[i]**dist[i+1])
    ans %= MOD

print(ans)