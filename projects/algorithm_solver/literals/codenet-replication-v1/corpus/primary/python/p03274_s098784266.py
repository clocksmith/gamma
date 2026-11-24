n,k=map(int,input().split())
add=list(map(int,input().split()))

ans=float("inf")
for l in range(n-k+1):
    r=l+k-1
    ans=min(ans,
            abs(add[l])+abs(add[l]-add[r]),
            abs(add[r])+abs(add[r]-add[l])
            )

#探索する量が少ないので全探索により答えを求めることができる

print(ans)