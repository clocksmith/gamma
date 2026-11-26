class Factorial:
    def __init__(self,n,mod):
        self.f=[1]
        self.mod=mod
        for i in range(1,n+1):
            self.f.append(self.f[-1]*i%mod)
        self.i=[pow(self.f[-1],mod-2,mod)]
        for i in range(1,n+1)[::-1]:
            self.i.append(self.i[-1]*i%mod)
        self.i.reverse()
    def factorial(self,i):
        return self.f[i]
    def ifactorial(self,i):
        return self.i[i]
    def comb(self,n,k):
        return self.f[n]*self.i[n-k]%self.mod*self.i[k]%self.mod if n>=k else 0
M=10**9+7
a,b,c,d=map(int,input().split())
comb=Factorial(c+d+2,M).comb
f=lambda r,c:comb(c+r+2,r+1)-c-r-2
print((f(c,d)-f(c,b-1)-f(a-1,d)+f(a-1,b-1))%M)