import math
N,A,B,C,D=map(int,input().split())
if (D*math.ceil((N/C)))>(B*math.ceil((N/A))) :
    print(B*math.ceil((N/A)))
else : 
    print(D*math.ceil((N/C)))

