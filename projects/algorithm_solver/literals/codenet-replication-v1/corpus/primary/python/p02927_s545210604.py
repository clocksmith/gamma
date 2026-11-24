M,D = map(int,input().split())
count=0
for i in range(1,M+1):
	for j in range(1,D+1):
		if j>=10:
			if i == (int(list(str(j))[0])*int(list(str(j))[1])):
				if int(list(str(j))[0]) >1 and int(list(str(j))[1]) >1:
					count +=1	
print(count)