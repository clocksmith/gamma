# AOJ 1054: Distorted Love
# Python3 2018.7.7 bal4u

while True:
	n = int(input())
	if n == 0: break
	input()   # w, h
	pag, dic = [], {}
	for i in range(n):
		nm, k = input().split()
		dic[nm] = i
		btn = []
		for j in range(int(k)):
			x1, y1, x2, y2, bnm = input().split()
			btn.append((int(x1), int(y1), int(x2), int(y2), bnm))
		pag.append((nm, btn))
	buf = [0]*2000
	now, sz = 0, 1
	m = int(input())
	for i in range(m):
		a = input().split()
		if a[0] == "back":
			if now > 0: now -= 1
		elif a[0] == "forward":
			if now < sz-1: now += 1
		elif a[0] == "show": print(pag[buf[now]][0])
		else:		# click
			x, y = int(a[1]), int(a[2])
			btn = pag[buf[now]][1]
			for x1, y1, x2, y2, nm in btn:
				if x1 <= x and x <= x2 and y1 <= y and y <= y2:
					now += 1
					buf[now] = dic[nm]
					sz = now+1
					break

