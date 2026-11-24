n = int(input())

sList = []
for i in range(n):
  sList.append(input())

cList = []
sN = ord('a')
while True:
  if ord('z')+1 == sN:
    break
  sA = 50
  for i in range(n):
    tmp = sList[i].count(chr(sN))
    if sA > tmp:
      sA = tmp
  cList.append(sA)
  sN += 1

cS = ''
for i in range(len(cList)):
  cS += chr(ord('a')+i)*cList[i]
  
 
print(cS)
 