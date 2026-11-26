n = int(input())

c = 0

for i in range(25):
	for j in range(15):
		if i*4+j*7 == n:
			c += 1
	
		if i*4+j*7 >100:
			break
  
if c != 0:
	print('Yes')
else:
	print('No')