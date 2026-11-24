def get_sieve_of_eratosthenes_new(n):
    import math
    if not isinstance(n, int):
        raise TypeError('n is int type.')
    if n < 2:
        raise ValueError('n is more than 2')
    prime = []
    limit = math.sqrt(n)
    data = [i + 1 for i in range(1, n)]
    while True:
        p = data[0]
        if limit <= p:
            return prime + data
        prime.append(p)
        data = [e for e in data if e % p != 0]

def Ind(b,n):
    count=0
    while n%b==0:
        count+=1
        n//=b
    return count

prime=get_sieve_of_eratosthenes_new(10**4+1)

from fractions import gcd

N=int(input())
a=[]
for i in range(N+1):
    a.append(int(input()))

a=a[::-1]
ans=set([])
for p in prime:
    data=[0 for i in range(p)]
    for i in range(1,N+1):
        data[(i-1)%(p-1)]+=a[i]%p
        data[(i-1)%(p-1)]%=p
    check=(a[0]%p==0)
    for i in range(p):
        check=check&(data[i]%p==0)
    if check:
        ans.add(p)


n=a[0]
for i in range(N+1):
    n=gcd(n,a[i])

prime=get_sieve_of_eratosthenes_new(32000)

for p in prime:
    i=Ind(p,n)
    if i!=0:
        ans.add(p)
    n//=pow(p,i)

if abs(n)!=1:
    ans.add(abs(n))

ans=list(ans)
ans.sort()
for i in range(len(ans)):
    print(ans[i])
