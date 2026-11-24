N, M = map(int, input().split())
A = [int(input()) for i in range(N)]  #費用
R = [0]*N  #投票数
for _ in range(M):
	B = int(input())
	for i in range(len(A)):
		if B>=A[i]:
			R[i] += 1
			break

#print(R)
maxvalue = max(R)
for i in range(len(R)):
	if maxvalue==R[i]:
		print(i+1)
		exit(0)

