def print_tmp(a_li):
    s = [str(a) for a in a_li]
    t = ' '.join(s)
    print(t)


n = int(input())
a = input()
A = [int(i) for i in a.split(' ')]
print_tmp(A)
for i in range(1, n):
    v = A[i]
    j = i -1
    while j >= 0 and A[j] > v:
        A[j+1] = A[j]
        j -= 1
    A[j+1] = v
    print_tmp(A)

