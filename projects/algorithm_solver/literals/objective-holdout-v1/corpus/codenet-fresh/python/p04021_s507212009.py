n = int(input())
nums = []
evens = set()
for i in range(n):
  tmp = int(input())
  nums.append(tmp)
  if i%2==0:
    evens.add(tmp)
nums.sort()
count = 0
for j in range(n):
  if j%2 == 0:
    if nums[j] not in evens:
      count += 1
print(count)