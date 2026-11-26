n=int(input())
a=list(map(int,input().split()))
x=a[0]
y=sum(a)-a[0]
mini=float('inf')
if n==2:
    print(abs(a[0]-a[1]))
    exit()
for i in range(1,n-1):
    x+=a[i]
    y-=a[i]
    mini=min(mini,abs(x-y))
print(mini)