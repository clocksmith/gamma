function solve(nums, k) {
  // O(n) time and auxiliary space; no input mutation.
  const length = nums.length;
  const suffixMinimum = new Array(length);
  let minimum = nums[length - 1];
  for (let index = length - 1; index >= 0; index--) {
    minimum = Math.min(minimum, nums[index]);
    suffixMinimum[index] = minimum;
  }
  let maximum = nums[0];
  for (let index = 0; index < length; index++) {
    maximum = Math.max(maximum, nums[index]);
    if (maximum - suffixMinimum[index] <= k) return index;
  }
  return -1;
}
