for i in range(int(input())):
	ax, ay, bx, by, cx, cy, dx, dy = map(float, input().split())
	if ax==bx or cx==dx:
		print("YES" if ax==bx and cx==dx and ay!=by and cy!=dy else "NO")
	else:
		print("YES" if abs((ay-by)/(ax-bx)-(cy-dy)/(cx-dx))<1e-10 else "NO")
