MOD=10**9+7
N=int(input())
x=list(map(int, input().split()))
y=[x[i+1]-x[i] for i in range(N-1)]
 
upp=[1]*(N+1)
for i in range(2, N+1):
  upp[i]=upp[i-1]*i
  upp[i]%=MOD
  
a=[0]*(N-1)
a[0]=upp[N-1]
for i in range(1, N-1):
  a[i]=a[0]*pow(i+1, MOD-2, MOD)
  a[i]%=MOD

b=[0]*(N-1)
b[0]=a[0]
for i in range(1, N-1):
  b[i]=b[i-1]+a[i]
  b[i]%=MOD
  
def moddot(v1, v2):
  n=len(v1)
  out=0
  for i in range(n):
    out+=v1[i]*v2[i]%MOD
    out%=MOD
  return out
 
ex=moddot(b, y)
print(ex)