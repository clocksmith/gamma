function solve(nums) {
  // O(n) time and auxiliary space; preserve order and repeated values.
  const valid = new Array(nums.length).fill(false);
  let maximum = -1;
  for (let index = 0; index < nums.length; index++) {
    if (nums[index] > maximum) valid[index] = true;
    maximum = Math.max(maximum, nums[index]);
  }
  maximum = -1;
  for (let index = nums.length - 1; index >= 0; index--) {
    if (nums[index] > maximum) valid[index] = true;
    maximum = Math.max(maximum, nums[index]);
  }
  return nums.filter((_, index) => valid[index]);
}
