N = int(input())

X = N // 11
M = N % 11
if M == 0:
    print(X * 2)
elif M > 6:
    print(X * 2 + 2)
else:
    print(X * 2 + 1)
