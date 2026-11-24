n,a,b=map(int,input().split())
X=list(map(int,input().split()))
Y=[0]*(n-1)
cnt=0
for i in range(n-1):
    Y[i]=X[i+1]-X[i]
    if a*Y[i]>=b:
        cnt+=b
    else:
        cnt+=a*Y[i]
print(cnt)