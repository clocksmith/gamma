# AOJ 1077: The Great Summer Contest
# Python3 2018.7.10 bal4u

while True:
	n, k, f = [0]*3, [0]*3, [0]*3
	a = list(map(int, input().split()))
	if sum(a) == 0: break
	for i in range(3): n[i] += a[i]+a[3+i]
	ans = 0
	for i in range(3):
		if n[i] >= 3: f[i] = 1
		ans += n[i]//3
		n[i] %= 3
		k[n[i]] += 1
	if k[0] > 0:
		if k[2] == 2:
			i = 0
			while n[i]: i += 1
			if f[i]: ans += 1
	elif k[1] > 0: ans += 1
	elif k[2] > 0: ans += 2
	print(ans)
