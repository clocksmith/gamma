#Partition
import math
N,M = map(int,input().split())
n = 1
rootM = int(math.sqrt(M))+1
for i in range(rootM):
    if M % (i+1) == 0 and N*(i+1) <= M:
        if N*(M/(i+1)) <= M and n <= (M/(i+1)):
            n = M/(i+1)
        elif n <= i+1:
            n = i+1
        else:
            continue
print(int(n))