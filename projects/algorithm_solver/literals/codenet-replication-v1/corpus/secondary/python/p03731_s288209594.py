N,T=[int(i) for i in input().split()]
t=[int(i) for i in input().split()]

res = T
for i in range(N-1):
    diff = t[i+1] - t[i]
    if diff<T:
        res+=diff
    else:
        res+=T
print(res)
