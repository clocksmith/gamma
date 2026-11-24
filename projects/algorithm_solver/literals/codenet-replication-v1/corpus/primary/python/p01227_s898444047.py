def croad():
    n,k = map(int,input().split())
    x = list(map(int,input().split()))
    y = []
    for i in range(n-1):
        y.append(x[i+1]-x[i])
    y.sort()
    y.reverse()
    while k>1 and len(y)>0:
        y.pop(0)
        k -= 1
    print(sum(y))

a = int(input())
for i in range(a):
    croad()
	
