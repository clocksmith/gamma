# AOJ 0229 Big Hit !
# Python3 2018.6.25 bal4u

while 1:
	b, r, g, c, s, t = map(int, input().split())
	if (b|r|g|c|s|t) == 0: break
	ans = 100
	ans += 15*b+(15-2)*5*b
	t -= 5*b
	ans += 15*r+(15-2)*3*r
	t -= 3*r
	ans += 7*g
	ans += 2*c
	t -= s
	ans -= 3*t
	print(ans);
