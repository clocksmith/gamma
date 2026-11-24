n,t,e = map(int,input().split())
x = list(map(int,input().split()))

ans=-1
for i in range(n):
    for j in range(x[i],10000000,x[i]):
        if t-e<=j and j<=t+e:
            ans = i+1
            
        elif j > t+e:
            break
print(ans)
