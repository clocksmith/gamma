def make_prime_table(n):
    """n以下の非負整数が素数であるかを判定したリストを出力する
    計算量: O(NloglogN)
    入出力例: 6 -> [False, False, True, True, False, True, False]
    """
    is_prime = [True] * (n + 1)
    is_prime[0] = False
    is_prime[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if not is_prime[i]:
            continue
        for j in range(2 * i, n + 1, i):
            is_prime[j] = False
    return is_prime


is_prime = make_prime_table(2 * 10 ** 6)
while True:
    n = int(input())
    if n == 0:
        break
    l = n
    r = n
    while not is_prime[l]:
        l -= 1
    while not is_prime[r]:
        r += 1
    print(r - l)
