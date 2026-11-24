N = int(input())
A = [int(x)-1 for x in input().split()]
B = [int(x) for x in input().split()]
C = [int(x) for x in input().split()]

total = 0
prev = -2
for a in A:
    total += B[a]
    if prev + 1  == a:
        total += C[a-1]
    prev = a
print(total)



