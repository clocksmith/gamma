def cmb(n, r, mod):
    if ( r<0 or r>n ):
        return 0
    r = min(r, n-r)
    return g1[n] * g2[r] * g2[n-r] % mod

x,y=map(int,input().split())

if (2*y-x)%3==0:
    a=(2*y-x)//3
    b=(2*x-y)//3
    mod = 10**9+7 #出力の制限
    N = a+b
    r=min(a,b)
    g1 = [1, 1] # 元テーブル
    g2 = [1, 1] #逆元テーブル
    inverse = [0, 1] #逆元テーブル計算用テーブル

    for i in range( 2, N + 1 ):
        g1.append( ( g1[-1] * i ) % mod )
        inverse.append( ( -inverse[mod % i] * (mod//i) ) % mod )
        g2.append( (g2[-1] * inverse[-1]) % mod )

    print(cmb(N,r,mod))
else:
    print(0)