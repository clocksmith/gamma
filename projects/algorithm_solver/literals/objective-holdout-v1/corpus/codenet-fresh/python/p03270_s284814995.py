import sys
input = sys.stdin.readline

mod = 998244353


def cmb(n, r, mod=mod):
    if ( r<0 or r>n ):
        return 0
    r = min(r, n-r)
    return g1[n] * g2[r] * g2[n-r] % mod

NN = 10**5 # 使うデータによって変える
g1 = [1, 1] # 元テーブル
g2 = [1, 1] #逆元テーブル
inverse = [0, 1] #逆元テーブル計算用テーブル

for i in range( 2, NN + 1 ):
    g1.append( ( g1[-1] * i ) % mod )
    inverse.append( ( -inverse[mod % i] * (mod//i) ) % mod )
    g2.append( (g2[-1] * inverse[-1]) % mod )


K, N = map(int, input().split())
for i in range(2, 2*K+1):
    if i%2 == 1:
        p = min(i//2, (2*K-i+1)//2)
        ans = 0
        t = 1
        for c in range(min(N,p)+1):
            ans = (ans + cmb(K+N-2*p-1, N-c) * cmb(p, c) * t) % mod
            t = t * 2 % mod
        print(ans)
    else:
        p = min(i//2-1, (2*K-i)//2)
        ans = 0
        t = 1
        for c in range(min(N,p)+1):
            ans = (ans + (cmb(K+N-2*p-3, N-c-1) + cmb(K+N-2*p-2, N-c)) * cmb(p, c) * t) % mod
            t = t * 2 % mod
        print(ans)