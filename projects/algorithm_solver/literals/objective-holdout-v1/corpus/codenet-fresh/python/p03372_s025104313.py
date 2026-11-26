import sys
input = sys.stdin.readline
from itertools import product
INF = 10**9
MOD = 10**9 + 7

def main():
    n,c = map(int,input().split())
    sushi = [list(map(int,input().split())) for _ in range(n)]
    
    r = [0] * (n+1)
    l = [0] * (n+1)
    r_max = [0] * (n+1)
    l_max = [0] * (n+1)

    x = 0
    y = c
    for i in range(n):
        r[i+1] = r[i] + sushi[i][1] - sushi[i][0] + x
        r_max[i+1] = max(r_max[i],r[i+1])
        x = sushi[i][0]

        l[-i-2] = l[-i-1] + sushi[-i-1][1] - y + sushi[-i-1][0]
        l_max[-i-2] = max(l_max[-i-1],l[-i-2])
        y = sushi[-i-1][0]
    
    ans = max(r_max[-1], l_max[0])
    for i in range(n-1):
        tmp1 = r[i+1] + l_max[i+1] - sushi[i][0]
        tmp2 = l[i+1] + r_max[i+1] - c + sushi[i+1][0]
        ans = max (ans ,tmp1 ,tmp2 )
    
    print(ans)
  
if __name__=='__main__':
    main()

