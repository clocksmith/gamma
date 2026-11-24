# ABC110 D factorization
N,M=map(int,input().split())
p=10**9+7
L=10**5*3
f,inv,finv=[0]*(L+1),[0]*(L+1),[0]*(L+1)

def factorization(N):
    res=[]
    for i in range(2,int(N**(1/2))+2):
        if not N%i:
            r=0
            while not N%i:
                N//=i
                r+=1
            res.append((i,r))
    if N>1:
        res.append((N,1))
    return res

def nCr_init(L,p):
    for i in range(L+1):
        if i<=1:
            f[i],finv[i],inv[i]=1,1,1
        else:
            f[i]=(f[i-1]*i)%p
            inv[i]=(p-inv[p%i]*(p//i))%p
            finv[i]=(finv[i-1]*inv[i])%p

def nCr(n,r,p):
    if 0<=r<=n and 0<=n:
        return (f[n]*finv[n-r]*finv[r])%p
    else:
        return 0

nCr_init(L,p)
p_list=factorization(M)
res=1
for a,r in p_list:
    res=(res*nCr(r+N-1,r,p))%p
print(res)