H = [False for i in range(1000001)]

H[1] = True
for i in range(20):
    for j in range(13):
        for k in range(9):
            if (2 ** i) * (3 ** j) * (5 ** k) < 1000001:
                H[(2 ** i) * (3 ** j) * (5 ** k)] = True
            else:
                break

while True:
    L = input()
    if L == "0":
        break

    a, b = [int(i) for i in L.split()]
    ans = 0
    for i in range(a, b+1):
        if H[i]:
            ans += 1
    print(ans)




