S = list(input())
cnt = 0
for i in S:
    if i == '+':
        cnt += 1
    else:
        cnt -= 1
print(cnt)