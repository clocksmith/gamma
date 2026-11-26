def solve(used,rest,sum,memo):
    
    if rest==0:
        return sum==0
    else:
        num=0
        for i in range(10):
            num*=2
            if used[i]:num+=1

        if (num,rest,sum) in memo:
            return memo[(num,rest,sum)]
        if sum<0:return 0
        ans=0
        for i in range(10):
            if not used[i]:
                used[i]=True
                ans+=solve(used,rest-1,sum-(i)*rest,memo)
                used[i]=False
        memo[(num,rest,sum)]=ans
        return memo[(num,rest,sum)]

memo={}
while True:
    try:
        n,s=map(int,input().split())
        used=[False for i in range(10)]
        ans=solve(used,n,s,memo)
        print(ans)
    except:
        break