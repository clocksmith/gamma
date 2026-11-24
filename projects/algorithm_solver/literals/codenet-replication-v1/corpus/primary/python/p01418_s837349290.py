import sys
sys.setrecursionlimit(10**9)
def input():
	return sys.stdin.readline()[:-1]

EPS = 1e-10
k, L, R = map(int, input().split())
p = float(input())
e = float(input())
t = float(input())

def search(l, r, prob, depth):
	#print(l, r, prob, depth) 
	if depth == k:
		h = (l+r)/2
		if abs(h-t) + EPS < e:
			return prob
		else:
			return 0
	else:
		if l - EPS > t + e or r + EPS < t - e:
			return 0
		elif l + EPS > t - e and t + e > r - EPS:
			return prob
		else:
			h = (l+r)/2
			if h >= t:
				return search(h, r, prob * p, depth+1) + search(l, h, prob * (1-p), depth+1)
			else:
				return search(h, r, prob * (1-p), depth+1) + search(l, h, prob * p, depth+1)

ans = search(L, R, 1, 0)
print('{:.12f}'.format(ans))
