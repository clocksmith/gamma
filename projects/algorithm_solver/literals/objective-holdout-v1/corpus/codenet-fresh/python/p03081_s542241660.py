import copy
import sys

n, q = map(int, sys.stdin.readline().split())

s = input()

leftLimit = -1
rightLimit = n

spells =   spell = sys.stdin.readlines()
  
for spell in reversed(spells):
  target, direction = spell.split()
  if direction == "R" and target == s[rightLimit - 1]:
    rightLimit -= 1
    if rightLimit <= 0:
      break
  try:
    if direction == "R" and target == s[leftLimit]:
      if leftLimit != -1:
         leftLimit -= 1
  except Exception as e:
    pass
  if direction == "L" and target == s[leftLimit + 1]:
    leftLimit += 1
    if leftLimit >= n-1:
      break
  try:  
    if direction =="L" and target == s[rightLimit]:
      if rightLimit != n:
        rightLimit += 1
  except Exception as e:
    pass
  #print(target, direction, leftLimit, rightLimit)

print(max(rightLimit - leftLimit - 1 , 0))
