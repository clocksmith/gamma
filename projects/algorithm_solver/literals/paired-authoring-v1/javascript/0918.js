class Solution {
  maxSubarraySumCircular(nums) {
    let total = nums[0];
    let maximum_end = nums[0];
    let minimum_end = nums[0];
    let maximum = nums[0];
    let minimum = nums[0];
    for (let index = 1; index < nums.length; index += 1) {
      const value = nums[index];
      maximum_end = Math.max(value, maximum_end + value);
      minimum_end = Math.min(value, minimum_end + value);
      maximum = Math.max(maximum, maximum_end);
      minimum = Math.min(minimum, minimum_end);
      total += value;
    }
    if (maximum < 0) {
      return maximum;
    }
    return Math.max(maximum, total - minimum);
  }
}
