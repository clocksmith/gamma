N = int(input())
dic = {1:0,2:0,4:0}
List = list(map(int,input().split()))
for item in List:
  if item%4 == 0:
    dic[4] += 1
  elif item %2 == 0:
    dic[2] += 1
  else:
    dic[1] += 1
Answer = 'No'
if dic[4] != 0 and dic[4]+1 >= dic[1]+dic[2]:
  Answer = 'Yes'
elif dic[4]>=dic[1]:
  Answer = 'Yes'
print(Answer)