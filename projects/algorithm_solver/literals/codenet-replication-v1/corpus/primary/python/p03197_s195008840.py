N = int(input())
A = [int(input())%2 for n in range(N)] 
 
for i in range(N):
    if A[i] == 1:
        print("first")
        break
else: print("second")