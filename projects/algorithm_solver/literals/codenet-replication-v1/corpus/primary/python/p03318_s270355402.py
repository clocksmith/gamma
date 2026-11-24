from math import log10
def nsn(N):
    K = sum( list( map( int, list( str(N)))))
    return N/K

def snuke(N):
    k = int( log10(N))+1
    s = N
    now = nsn(N)
    for d in range(k+1):
        x = (10**(d+1))*(N//(10**(d+1)) + 1) - 1
        y = nsn(x)
        if y < now:
            s = x
            now = y
    return s

K = int( input())
ans = 1
print(1)
for i in range(K-1):
    ans = snuke( ans + 1)
    print(ans)

