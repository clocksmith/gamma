import sys
input=sys.stdin.readline
n,t=list(map(int,input().split()))
a=list(map(int,input().split()))
ans=t
for i in range(1,n):
  if a[i]-a[i-1]<t:
    ans+=a[i]-a[i-1]
  else:
    ans+=t
print(ans)