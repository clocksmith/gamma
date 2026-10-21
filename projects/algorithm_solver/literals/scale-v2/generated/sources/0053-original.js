/* 53. Maximum Subarray */
function maxSubArray(nums) {
  let maximumSum = nums[0],
    currentSum = 0;
  for (const value of nums) {
    currentSum = Math.max(value, currentSum + value);
    maximumSum = Math.max(maximumSum, currentSum);
  }
  return maximumSum;
}
