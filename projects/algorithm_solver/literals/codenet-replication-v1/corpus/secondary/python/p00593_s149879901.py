# AOJ 1007: JPEG Compression
# Python3 2018.7.5 bal4u

import sys
from sys import stdin
input = stdin.readline

cno = 0
while True:
	n = int(input())
	if n == 0: break
	cno += 1
	a = [[0 for j in range(12)] for i in range(12)]
	m = k = f = 1;
	while True:
		if f:
			for r in range(k-1, -1, -1):
				a[r][k-1-r] = m
				m += 1
		else:
			for c in range(k-1, -1, -1):
				a[k-1-c][c] = m
				m += 1
		f = 1-f
		k += 1
		if k > n: break
	k = n-1
	while True:
		if f:
			for c in range(n-k, n):
				a[2*n-1-k-c][c] = m
				m += 1
		else:
			for r in range(n-k, n):
				a[r][2*n-1-k-r] = m
				m += 1
		f = 1-f
		k -= 1
		if k < 1: break
	print("Case ", cno, ":", sep='')
	for r in range(n):
		for c in range(n): print(format(a[r][c], "3d"), end='')
		print()
