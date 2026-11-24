# AOJ 2838: A-Z-
# Python3 2018.7.12 bal4u

S = input()
ans = p = 0
for s in S:
	k = ord(s)-ord('A')
	if k <= p: ans += 1
	p = k
print(ans)
