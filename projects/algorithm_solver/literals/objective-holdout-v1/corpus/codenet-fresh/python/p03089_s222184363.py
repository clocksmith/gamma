n = int(input())
bbb = list(map(int, input().split()))
for i, b in enumerate(bbb, start=1):
    if i < b:
        print(-1)
        exit()

ans = []
for _ in range(n):
    for i, b in reversed(list(enumerate(bbb, start=1))):
        if i == b:
            ans.append(i)
            bbb.pop(i - 1)
            break
ans.reverse()
print('\n'.join(map(str, ans)))
