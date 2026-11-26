N = int(input())
SP = []
for idx in range(N):
	tmp = input().split()
	tmp[1] = int(tmp[1])
	tmp.append(idx+1)
	SP.append(tmp)

sorted_items = sorted(
  SP,
  key = lambda sp: (sp[0], -1 * sp[1])
)
for item in sorted_items:
	print(item[2])