X,Y=map(int,input().split())
result=0
if X==1 :
  result+=300000
elif X==2:
  result+=200000
elif X==3:
  result+=100000
if Y==1 :
  result+=300000
elif Y==2:
  result+=200000
elif Y==3:
  result+=100000
if X==1 and Y==1:
  result+=400000
print(result)