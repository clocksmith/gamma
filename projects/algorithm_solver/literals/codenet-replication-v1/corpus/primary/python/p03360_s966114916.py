A = list(map(int, input().split()))
A.sort(reverse = True)
K = int(input())

print(A[0] * (2 ** K) + A[1] + A[2])