n, w = map(int, input().split())

if n*w==1:
    print(1)
elif n==1:
    print(w-2)
elif w==1:
    print(n-2)
elif n==2 or w==2:
    print(0)
else:
    print((n-2)*(w-2))
