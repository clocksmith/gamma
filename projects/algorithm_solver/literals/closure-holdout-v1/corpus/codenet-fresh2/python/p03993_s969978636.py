a = int(input())
b = [int(k) for k in input().split()]

count = 0
for i in range(0, a):
	if b[b[i] - 1] == i + 1:
		count += 1

print (int(count / 2))