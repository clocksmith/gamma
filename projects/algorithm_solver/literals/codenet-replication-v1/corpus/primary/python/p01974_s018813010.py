N = int(input())
a = [int(x) for x in input().split()]

x, y = -1, -1

for i in range(N) :
    for j in range(N) :
        if i != j and abs(a[i] - a[j]) % (N - 1) == 0 :
            x, y = i, j
            
print(a[x], a[y])

