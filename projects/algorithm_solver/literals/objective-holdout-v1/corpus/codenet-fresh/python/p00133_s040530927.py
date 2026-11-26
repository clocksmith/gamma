# AOJ 0133 Rotation of a Pattern
# Python3 2018.6.19 bal4u

a = [[[0 for c in range(8)] for r in range(8)] for k in range(4)]
title = ["0", "90", "180", "270"]

for r in range(8):
	a[0][r] = list(input())
for k in range(1, 4):
	print(title[k])
	for r in range(8):
		for c in range(8):
			a[k][c][7-r] = a[k-1][r][c]
	for r in range(8): print(*a[k][r], sep='')
