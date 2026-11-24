def bubbleSort(list):
  j = len(list) - 1
  bcnt = 0
  while j:
    for i in range(j):
      if list[i] > list[i + 1]:
        list[i], list[i + 1] = list[i + 1], list[i]
        bcnt += 1
    j -= 1
  return bcnt
 
while True:
  n = int(input())
  if n == 0:
    break
  A = []
  for _ in range(n):
    A.append(int(input()))
  print(bubbleSort(A))
