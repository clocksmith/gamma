#coding:utf-8

h = []
for i in range(10):
	h.append(int(input()))

h = sorted(h,reverse = True)
for i in h[:3]:
	print(i)