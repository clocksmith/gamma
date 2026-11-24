ab = [0 for _ in range(2001)]
for a in range(1001):
    for b in range(1001):
        ab[a+b] += 1

while True:
    try:
        n = int(input())
    except:
        break
    ans = sum(ab[i]*ab[n-i] for i in range(2001) if n-i >= 0 and  n-i <= 2000)
    print(ans)