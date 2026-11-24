s = input()
acgt = ['A', 'C', 'G', 'T']
s_list = list(s)

part_len = 0
max_len = 0

for s in s_list:
	if s in acgt:
		part_len += 1
		if part_len > max_len:
			max_len = part_len
	else:
		part_len = 0

print(max_len)