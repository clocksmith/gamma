N = int(input())
for h in range(1, 3501):
    for n in range(1, 3501):
        a = 4 * h * n - h * N - n * N
        if a == 0:
            break
        w = int((h * n * N) / a)
        if w > 0 and 4 / N == 1 / h + 1 / n + 1 / w:
            print(h, n, w)
            exit()