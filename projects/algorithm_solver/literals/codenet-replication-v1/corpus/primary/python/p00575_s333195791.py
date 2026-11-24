A,B,C=map(int,input().split())

coin=0

for day in range(1,C+1):
    coin+=A
    if day % 7 ==0:
       coin+=B
    if coin >=C:
       break
   
print(day)
