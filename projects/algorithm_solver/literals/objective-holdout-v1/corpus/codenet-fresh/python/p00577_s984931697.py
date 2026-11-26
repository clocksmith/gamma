num=int(input())
ox=input()
ans=0
while True:
    if len(ox)<=1:
        break
    a=ox.find("OX",0,2)
    b=ox.find("XO",0,2)
    if a==0 or b==0:
        ox=ox[2:]
        ans+=1
    else:
        ox=ox[1:]

print(ans)
