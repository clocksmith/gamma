n,k = map(int,input().split())
for i in range(1000000000):
    if (k**(i+1))-1>=n:
        print(i+1)
        break
