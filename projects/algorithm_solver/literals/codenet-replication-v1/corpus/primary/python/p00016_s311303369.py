import math

if __name__ == '__main__':

	x = y = 0
	deg = 90

	while True:

		d,a = map(int,input().split(","))
		if d == 0 and a == 0:
			break

		x += math.cos(math.radians(deg)) * d
		y += math.sin(math.radians(deg)) * d

		deg -= a

	print(int(x))
	print(int(y))

