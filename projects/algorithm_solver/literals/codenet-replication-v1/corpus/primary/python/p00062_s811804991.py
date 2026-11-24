def solve(nums):
  while len(nums) > 1:
    nums = [nums[i] + nums[i + 1] for i in range(len(nums) -1)]
  return nums[0] % 10

while True:
  try:
    s = list(map(int, list(input())))
    print(solve(s))

  except EOFError:
    break

