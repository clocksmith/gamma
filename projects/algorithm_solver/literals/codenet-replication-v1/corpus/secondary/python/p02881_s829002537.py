import math
N=int(input())

start=int(math.sqrt(N))+1

end=0
while start>0:
    if N%start==0:
        end=N//start
        break
    else:
        start-=1

print(end-1+start-1)