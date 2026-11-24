import sys
sys.setrecursionlimit(100000)

def load_fields():
	fields = []
	i = 0
	H, W = 0, 0
	field = []
	for line in sys.stdin:
		line = line.rstrip()
		if line[0] not in ["#", "@", "*"]:
			line = line.split(" ")
			H = int(line[0])
			W = int(line[1])
			if (len(field) != 0):
				fields.append(field)
				field = []
			if (H == 0 and W == 0):
				break

		else:
			field.append(list(line))
		i += 1
	return fields

def dfs(x, y, fruit):
	field[x][y] = "0"
	for dx in [-1, 0, 1]:
		if dx == -1: width = [0]
		if dx == 0: width = [-1, 0, 1]
		if dx == 1: width = [0]
		for dy in width:
			nx = x+dx
			ny = y+dy
			inField = (0 <= nx) and (0 <= ny) and (nx < H) and (ny < W)
			if inField and field[nx][ny] == fruit:
				dfs(nx, ny, fruit)
				
fields = load_fields()
count = 0
for field in fields:
	H = len(field)
	W = len(field[0])
	for x in range(H):
		for y in range(W):
			if (field[x][y] != "0"):
				dfs(x, y, field[x][y])
				count += 1
	print(count)
	count = 0