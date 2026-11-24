N = int(input())
a = list(map(int, input().split()))
b = list(map(int, input().split()))

d_pls = []
d_mns = []
s = 0
for i in range(N):
    t = a[i] - b[i]
    s += t
    if t > 0:
        d_pls.append(t)
    elif t < 0:
        d_mns.append(t)
# 準備不足なら負

if s < 0:
    print(-1)
    exit()

d_pls = sorted(d_pls, reverse=True)

d_mns = sorted(d_mns)
m_sum = sum(d_mns)
ans = len(d_mns)

i = 0
while m_sum < 0:
    m_sum += d_pls[i]
    ans += 1
    i += 1
print(ans)
