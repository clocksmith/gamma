while True:
    n = int(input())
    if n == 0:
        break
    line = list(map(int, input().split()))
    i = 0
    while i < n:
        j = i
        while j+1 < n and line[j+1]-line[j] == 1:
            j += 1
        s = "\n" if n-1 == j else " "
        if i == j:
            print("%d%s" % (line[i], s), end='')
            i += 1
        else:
            print("%d-%d%s" % (line[i], line[j], s), end='')
            i = j+1