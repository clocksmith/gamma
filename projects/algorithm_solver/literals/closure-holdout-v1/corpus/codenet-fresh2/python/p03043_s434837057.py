import math

def main():
    n,k=list(map(int,input().split(' ')))
    ans = 0
    for i in range(1,min(n+1,k)):
        ans +=(1/2)**(-(math.log2(k/i)//-1))
    if n >= k:
        ans += (n-k+1)
    print(ans/n)

main()