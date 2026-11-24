n_a = int(input())
a = [int(i) for i in input().split()]
n_b = int(input())
b = [int(j) for j in input().split()]

if set(a)&set(b) == set(b):
	print('1')
else:
	print('0')
