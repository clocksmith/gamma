def solve(n,m):
	A=[i for i in range(1,n+1)]
	i=n-1
	while True:
		if len(A)==1:
			break
		i=(i+m)%len(A)
		A.pop(i)
		i=i-1 if i>0 else len(A)-1
	return A[0]




while True:
	n,m=map(int,input().split())
	if n==m==0:
		break
	print(solve(n,m))