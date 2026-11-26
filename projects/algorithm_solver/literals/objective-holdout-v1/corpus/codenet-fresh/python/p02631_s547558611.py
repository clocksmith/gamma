n = int(input())
a = list(map(int,input().split()))

a_xor = 0
for i in a:
    a_xor = a_xor^i

ans = []
for i in a:
    ans.append(a_xor^i)

for i in ans:
    print(i, end=" ")