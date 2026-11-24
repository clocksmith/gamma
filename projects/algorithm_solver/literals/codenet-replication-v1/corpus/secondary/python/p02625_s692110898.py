MOD=10**9+7
def facinv(N):
    fac,finv,inv=[0]*(N+1),[0]*(N+1),[0]*(N+1)
    fac[0]=1;fac[1]=1;finv[0]=1;finv[1]=1;inv[1]=1
    for i in range(2,N+1):
        fac[i]=fac[i-1]*i%MOD
        inv[i]=MOD-inv[MOD%i]*(MOD//i)%MOD
        finv[i]=finv[i-1]*inv[i]%MOD
    return fac,finv,inv

def COM(n,r):
    if n<r or r<0:
        return 0
    else:
        return ((fac[n]*finv[r])%MOD*finv[n-r])%MOD

def PER(n,r):
    if n<r or r<0:
        return 0
    else:
        return (fac[n]*finv[n-r]%MOD)

N,M=map(int,input().split())
fac,finv,inv=facinv(M)

ans=PER(M,N)**2%MOD
res=0
for r in range(1,N+1):
    f=COM(N,r)*PER(M,r)%MOD*(PER(M-r,N-r)**2%MOD)%MOD
    res=(res+(pow(-1,r-1)*f)+MOD)%MOD
print((ans-res+MOD)%MOD)