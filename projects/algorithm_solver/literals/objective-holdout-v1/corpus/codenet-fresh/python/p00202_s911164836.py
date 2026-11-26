
def solve(price, ps, is_prime):
    dp = [0] * ((price >> 5) + 1)
    for i in range(0, price + 1,ps[0]):
        dp[i >> 5] |= 1 << (i & 31)
    dp[0] = 1
    for i in range(1, len(ps)):
        cur_p = ps[i]
        r = cur_p & 31
        rest = 0
        if cur_p >= 32:
            for p in range(cur_p, price + 1, 32):
                i1 = (p - cur_p) >> 5
                i2 = p >> 5
                v = dp[i1]
                dp[i2] |= ((v << r)&(2**33-1)) | rest
                rest = (v >> (32 - r)) & ((1 << r) - 1)
        else:
            for p in range(cur_p, price + 1):
                dp[p >> 5] |= (dp[(p - cur_p) >> 5] >> ((p - cur_p) & 31) & 1) << (p & 31)

    p = -1
    for i in range(price+1, 0,-1):
        if is_prime[i] and (dp[i >> 5] >> (i & 31) & 1):
            p = i
            break
    if p == -1:
        print("NA")
    else:
        print(p)
     
def main():
    N = 1000001
    temp = [True]*(N+1)
    temp[0] = temp[1] = False
    for i in range(2, int((N+1)**0.5)+1):
        if temp[i]:
            temp[i+i::i] = [False]*(len(temp[i+i::i]))

    while True:
        n, price = map(int,input().split())
        if n == 0 and price == 0:
            return
        ps = []
        for i in range(n):
            ps.append(int(input()))
        solve(price, ps, temp)
 
main()
