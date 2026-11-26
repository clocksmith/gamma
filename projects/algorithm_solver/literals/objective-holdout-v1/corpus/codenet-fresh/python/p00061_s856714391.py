P = [-1] * 101
while True:
    t, p = [int(x) for x in input().split(",")]
    if t == 0 and p == 0:
        break
    P[t] = p

L = sorted(set(P),reverse=True)
#print(L)
d = dict()
for rank, point in enumerate(L,start=1):
    d[point] = rank
#print(d)
while True:
    try:
        t = int(input())
    except:
        break

    p = P[t]
    print(d[p])


    



