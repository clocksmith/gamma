A,B,K = (int(x) for x in input().split())

while K != 0:
    if A % 2 !=0:
        A -= 1
    A = A/2
    B += A
    K -= 1

    if K ==0:
        break
    if B % 2 !=0:
        B -= 1
    B = B/2
    A += B
    K -= 1

A = int(A)
B = int(B)
print(A,B)