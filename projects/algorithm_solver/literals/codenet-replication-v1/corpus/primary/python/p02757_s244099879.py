n, p = map(int, input().split())
s = input()

if p == 2 or p == 5:
    ans = 0
    for i in range(n):
        if int(s[i]) % p == 0:
            ans += i + 1
else:
    s2 = s[::-1]
    rems = [0]
    tmp = 0
    tmp2 = 1
    for i in range(n):
        tmp += int(s2[i]) * tmp2
        tmp %= p
        tmp2 *= 10
        tmp2 %= p
        rems.append(tmp)

    from collections import Counter
    counter = Counter(rems)
    ans = 0
    for key in counter.keys():
        v = counter[key]
        ans += v * (v - 1) // 2
print(ans)
