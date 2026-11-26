n,c=map(int,input().split())
p=[int(i) for i in input().split()]
cake=sum(p)
ans=divmod(cake,n+1)
print(ans[0] if ans[1]==0 else ans[0]+1)
