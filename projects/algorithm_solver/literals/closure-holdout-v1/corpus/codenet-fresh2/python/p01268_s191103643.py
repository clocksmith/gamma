import bisect
MAX_N = 120000
sieve = [0,0] + [1] * MAX_N
n = 2
primes = []
while n*n < MAX_N:
    if sieve[n]:
        primes.append(n)
        for m in range(2*n,MAX_N,n):
            sieve[m] = 0
    n += 1
for m in range(n,MAX_N):
    if sieve[m]: primes.append(m)

while True:
    N,P = map(int,input().split())
    if N == -1: break
    i = bisect.bisect_right(primes, N)
    li = []
    for p1 in range(i,i+P):
        for p2 in range(p1,i+P+1):
            li.append(primes[p1] + primes[p2])
    print(sorted(li)[P-1])