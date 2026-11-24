N = int(input())
W = [input() for i in range(N)]

result = True

for i in range(1, N):
    if W[i-1][-1] != W[i][0]:
        result = False
        break
    if W[i] in W[:i]:
        result = False
        break

if result:
    print("Yes")
else:
    print("No")
