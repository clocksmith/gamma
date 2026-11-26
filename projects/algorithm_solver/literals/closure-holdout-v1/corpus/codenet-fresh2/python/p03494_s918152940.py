N = int(input())
nums = [int(x) for x in input().split()]
cnt = 0
loop = True
while loop:
  if not all([n % 2 is 0 for n in nums]):
     
    break
    
  for i, n in enumerate(nums):
    nums[i] = n//2
  cnt += 1
print(cnt)