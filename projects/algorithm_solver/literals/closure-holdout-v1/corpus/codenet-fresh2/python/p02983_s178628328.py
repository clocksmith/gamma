L,R=map(int, input().split())
m = 2020
for i in range(L,R+1):
    for j in range(L+1,R+1):
        if i == j:
            continue
        if i*j%2019 < m:
            m = i*j%2019
        if m == 0:
            break
    if m == 0:
        break
print(m)