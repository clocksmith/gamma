# AOJ 0631: Point Card
# Python3 2018.7.2 bal4u

n, m = map(int, input().split())
ans, mi = 0, n*2
for i in range(m):
	a, b = map(int, input().split())
	if a < n:
		ans += n-a
		mi = min(mi, a)
print(ans if ans <= 0 else ans-(n-mi));

