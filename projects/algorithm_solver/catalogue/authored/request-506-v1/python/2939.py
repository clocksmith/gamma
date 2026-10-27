# Original candidate. Contract: https://leetcode.com/problems/maximum-xor-product/
def solve(a, b, n):
    mask=(1<<n)-1;u=a&~mask;v=b&~mask
    for i in range(n-1,-1,-1):
        bit=1<<i
        if (a&bit)==(b&bit):u|=bit;v|=bit
        elif u<v:u|=bit
        else:v|=bit
    return u*v%1000000007
