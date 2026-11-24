
W,H = map(int,input().split())

t = H+1
y = W+1

ans = 0

lis = []

for i in range(W):
    p = int(input())
    lis.append([p,"y",i])

for i in range(H):
    q = int(input())
    lis.append([q,"t",i])

lis.sort()

for i in lis:

    ncost = i[0]
    ndir = i[1]
    #print (i,ans)

    if ndir == "t":
        t -= 1
        ans += ncost * max(0 , y)

    else:
        y -= 1
        ans += ncost * max(0 , t)

print (ans)
