N = int(input())
X = input()
MOD = 998244353

ans = 0
memo = dict()

# def get_divisor(n):
#     '''nの約数を返す
#     '''
#     d = set()
#     for i in range(1, int(n**0.5)+1):
#         if n % i == 0:
#             d.add(i)
#             d.add(n//i)
#     return d

def get_oddivisor(n):
    '''nの約数のうち商が奇数のものを返す
    '''
    d = set()
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            if i%2 == 1:
                d.add(n//i)
            if (n//i)%2 == 1:
                d.add(i)
    return d

D = list(get_oddivisor(N))
D.sort()

def alternate(x, n):
    '''x: 00101, y: 11010, z: (00101)(11010)... n times
    '''
    y = ('0'*len(x) + bin(int(x,2) ^ (2**len(x)-1))[2:])[-len(x):]
    z = (x + y) * (n//2)
    if n%2 == 1:
        z += x
    return z

for d in D:
    cnt = int(X[:d], 2)
    if int(X, 2) >= int(alternate(X[:d], N//d), 2):
        cnt += 1
    dd = list(get_oddivisor(d))
    for ddd in dd:
        if ddd != d:
            cnt -= memo[ddd]
    memo[d] = cnt
    ans += cnt * 2 * d
    ans %= 998244353

print(ans)
