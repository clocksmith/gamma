# AOJ 1111: Cyber Guardian
# Python3 2018.7.15 bal4u

import re
while True:
	n, m = map(int, input().split())
	if (n|m) == 0: break
	rule, ans = [], []
	for i in range(n):
		g, s, d = input().split()
		rule.append((g[0] == 'p', re.compile((s+d).replace("?", "[0-9]"))))
	for i in range(m):
		s, d, m = input().split()
		sd = s+d
		for G, SD in rule[::-1]:
			if re.match(SD, sd):
				if G: ans.append((s, d, m))
				break
	print(len(ans))
	for a in ans: print(*a)

