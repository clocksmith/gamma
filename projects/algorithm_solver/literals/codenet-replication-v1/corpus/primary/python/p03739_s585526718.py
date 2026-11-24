n = int(input())
a = list(int(i) for i in input().split())  
ctplus = 0
ctminu = 0
checksum = 0
for i in range(n):
  checksum += a[i]
  if i%2 ==0:
    if checksum <= 0:
      ctplus += abs(checksum)+1
      checksum += abs(checksum)+1
  else:
    if checksum >= 0:
      ctplus += abs(checksum)+1
      checksum -= (abs(checksum)+1)
checksum = 0
for j in range(n):
  checksum += a[j]
  if j%2 ==1:
    if checksum <= 0:
      ctminu += abs(checksum)+1
      checksum += abs(checksum)+1
  else:
    if checksum >= 0:
      ctminu += abs(checksum)+1
      checksum -= (abs(checksum)+1)      
print(min(ctplus,ctminu))