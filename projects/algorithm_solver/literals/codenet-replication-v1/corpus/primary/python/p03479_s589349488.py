X, Y = map(int,input().split())
counter = 0
K=X
i = 0
while K <=Y:
  counter += 1
  K *= 2
  
print(counter)