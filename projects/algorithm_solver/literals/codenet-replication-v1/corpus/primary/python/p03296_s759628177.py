n=int(input())
a=list(map(int,input().split()))
ans=0
now=a[0]
cnt=1
i=1
for i in range(1,n):
    if(a[i]==now):
        cnt+=1
    else:
        ans+=cnt//2
        cnt=1
        now=a[i]
ans+=cnt//2
print(ans)