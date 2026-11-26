n = int(input())
ans = 0
for i in range(1,int(n**0.5) + 1):
    if n % i == 0:
        a = n//i - 1
        b = i - 1
        #print("{} {}".format(b,a))
        if a != 0 and (n // a) == n % a:
            ans += a
        if b != 0 and (n // b) == n % b:
            ans += b
print(ans)