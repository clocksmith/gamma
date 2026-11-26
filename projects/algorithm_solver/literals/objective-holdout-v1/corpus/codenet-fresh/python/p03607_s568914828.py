n=int(input())
a= [int(input()) for i in range(n)] 

a.sort()
ans=0
m=1

for i in range(1,n):
    if a[i-1] == a[i]:
        m+=1
    else:
        ans+=(m%2)
        m=1

ans+=(m%2)

print(ans)
