# AOJ 1114: Get a Rectangular Field
# Python3 2018.7.8 bal4u

s = [[0 for c in range(6)] for r in range(6)]
for k in range(int(input())):
	if k > 0: input()
	for r in range(5):
		a = list(map(int, input().split()))
		for c in range(5): s[r+1][c+1] = s[r+1][c]+a[c]
	ans = 0;
	for r in range(1, 6):
		for c in range(1, 6):
			for c2 in range(5, c-1, -1):
				w2 = w = c2-c+1
				if w2 > s[r][c2]-s[r][c-1]: continue
				ans = max(ans, w2)
				for r2 in range(r+1, 6):
					if w > s[r2][c2]-s[r2][c-1]: break
					w2 += w
					ans = max(ans, w2)
	print(ans)

