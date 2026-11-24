n = int(input())

for _ in range(n):
    start, end = map(int, input().split())

    anslist = []
    if start <= 5:
        if start > end:
            [anslist.append(i) for i in range(start, end-1, -1)]
        else:
            [anslist.append(i) for i in range(start, end+1)]
    elif start < end:
        [anslist.append(i) for i in range(start, end+1)]
    else:
        [anslist.append(i) for i in range(start, 10)]
        if end <= 5:
            [anslist.append(i) for i in range(5, end-1, -1)]
        else:
            [anslist.append(i) for i in range(5, 0, -1)]
            [anslist.append(i) for i in range(0, end+1)]

    print(' '.join(str(ans) for ans in anslist))
