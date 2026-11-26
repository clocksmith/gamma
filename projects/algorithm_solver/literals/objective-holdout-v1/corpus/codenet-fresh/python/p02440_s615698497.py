input()
A = list(map(int, input().split()))
q = int(input())
for _ in range(q):
    query = list(map(int, input().split()))
    if query[0] == 0:
        print(min(A[query[1]:query[2]]))
    else:
        print(max(A[query[1]:query[2]]))
