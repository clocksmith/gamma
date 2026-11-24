N = int(input())
flag = 1
for a in range(-119, 119):
    for b in range(-119, 119):
        if a**5 - b**5 == N:
            A = str(a)
            B = str(b)
            flag = 0
    if flag ==0:
        break
print(A + " " +B)