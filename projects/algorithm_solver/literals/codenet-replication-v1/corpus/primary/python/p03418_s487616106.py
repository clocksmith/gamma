n, k = map(int, input().split())		# 5 7


if k==0:
	print(n*n)
	exit(0)

ans = 0
for i in range(k+1, n+1):
	q = n // i
	m = n % i
	
	a = q*(i-k)
	b = max(m-k+1, 0)
	
	#print(i, q,m,a,b)
	
	ans += a+b

print(ans)
