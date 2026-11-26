n = int(input())
listed = list(map(int,input().split()))

length2 = len(set(listed))

if n == length2:
    print('YES')
else:
    print('NO')