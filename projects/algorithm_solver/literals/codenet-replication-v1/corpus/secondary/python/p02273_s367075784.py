import math

n = int(input())
p0 = (0,0)
p1 = (100,0)

def koch(depth, p0, p1):

	if depth == 0:
		return

	sx = (2*p0[0] + 1*p1[0]) / 3
	sy = (2*p0[1] + 1*p1[1]) / 3
	s = (sx,sy)
	tx = (1*p0[0] + 2*p1[0]) / 3
	ty = (1*p0[1] + 2*p1[1]) / 3
	t = (tx,ty)

	theta = math.radians(60)
	ux = (tx - sx)*math.cos(theta) - (ty - sy)*math.sin(theta) + sx
	uy = math.sin(theta) * (tx - sx) + math.cos(theta) * (ty - sy) + sy
	u = (ux, uy)

	#各辺でkoch関数を適用することにより、頂点を出力。出力したい部分に噛ませる。
	koch(depth-1,p0,s)
	print(*s)
	koch(depth-1,s,u)
	print(*u)
	koch(depth-1,u,t)
	print(*t)
	koch(depth-1,t,p1)
	

print(*p0)
koch(n,p0,p1)
print(*p1)
