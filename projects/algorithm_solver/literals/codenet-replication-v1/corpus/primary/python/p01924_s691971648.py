# AOJ 2824: Coastline
# Python3 2018.7.11 bal4u

while True:
	T, D, L = map(int, input().split())
	if T == 0: break
	a = []
	for i in range(T):
		x = int(input())
		if x >= L: a.append(i)
	T, ans = T-1, 0
	for i in range(1, len(a)):
		x = D
		if T-a[i-1] < D: x = T-a[i-1]
		if a[i]-a[i-1] < x: ans += a[i]-a[i-1]
		else: ans += x
	if a: ans += T-a[-1] if a[-1]+D > T else D
	print(ans)

