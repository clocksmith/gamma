
NM=input().split()

N=int(NM[0])
M=int(NM[1])

s=[]
a=[]

for i in range(N-1):
    s.append(int(input()))

Sum=0
TotalS=[0]

for i in range(N-1):
    Sum+=s[i]
    TotalS.append(Sum)

position=0
TD=0#TraveledDistance

for i in range(M):
    a=int(input())
    TD+=abs(TotalS[position]-TotalS[position+a])
    position+=a

TD%=100000
print(TD)


