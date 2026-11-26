n, t = list(map(int, input().split()))
a = list(map(int, input().split()))
min_a = 1000000000
max_dif = 0
max_dif_c = 0
for i in range(n):
    if a[i] < min_a:
        min_a = a[i]
    elif a[i] - min_a > max_dif:
        max_dif = a[i] - min_a
        max_dif_c = 1
    elif a[i] - min_a == max_dif:
        max_dif_c += 1
print(str(max_dif_c))
