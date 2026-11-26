m, f, b = map(int, input().split())

if m >= b :
    print(0)
elif m+f >= b :
    print(b-m)
else :
    print('NA')
