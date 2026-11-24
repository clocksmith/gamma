from collections import deque
N, K = map(int, input().split())
a = list(map(int, input().split()))
ans = 1
c = 0
d = 0
q = deque()
p = deque()
for i in range(K):
    if len(q) == 0:
        q.append(i)
    else:
        while len(q) > 0:
            if a[q[len(q)-1]] > a[i]:
                q.pop()
            else:
                q.append(i)
                break
        else:
            q.append(i)

    if len(p) == 0:
        p.append(i)
    else:
        while len(p) > 0:
            if a[p[len(p)-1]] < a[i]:
                p.pop()
            else:
                p.append(i)
                break
        else:
            p.append(i)
    if len(q) == K:
        c += 1

for i in range(K, N):
    if len(q) == 0:
        q.append(i)
    else:
        flag = 0
        while len(q) > 0:
            if a[q[len(q)-1]] > a[i]:
                q.pop()
                flag = 1
            else:
                q.append(i)
                break
        else:
            q.append(i)
        if q[0] == i-K:
            l = q.popleft()
        else:
            flag = 1

    if len(p) == 0:
        p.append(i)
    else:
        while len(p) > 0:
            if a[p[len(p)-1]] < a[i]:
                p.pop()
            else:
                p.append(i)
                break
        else:
            p.append(i)
        if a[p[0]] > a[i]:
            flag = 1

        if p[0] == i-K:
            l = p.popleft()



    if flag == 1:
        ans += 1
    if len(q) == K and flag == 1:
        c += 1

if c > 1:
    ans -= c-1
print(ans)
