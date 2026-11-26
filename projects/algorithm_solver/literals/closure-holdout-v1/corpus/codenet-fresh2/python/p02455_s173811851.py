q = int(input())

num = set()
for _ in range(q):
    query, x = map(int, input().split())
    if query == 0:
        num.add(x)
        print(len(num))
    elif query == 1:
        if x in num:
            print(1)
        else:
            print(0)

