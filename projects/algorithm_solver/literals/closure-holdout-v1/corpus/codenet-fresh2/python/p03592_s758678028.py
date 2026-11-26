n, m, k = list(map(int, input().split()))

p = False
for ni in range(m+1):
    for mi in range(n+1):
        if k == ni*n + mi*m - 2*(ni*mi):
            p = True
            break

print("Yes" if p else "No")