class Solution {
  isMonotonic(nums) {
    let increasing = true;
    let decreasing = true;
    for (let index = 1; index < nums.length; index += 1) {
      if (nums[index] < nums[index - 1]) {
        increasing = false;
      }
      if (nums[index] > nums[index - 1]) {
        decreasing = false;
      }
      if (!increasing && !decreasing) {
        return false;
      }
    }
    return true;
  }
}
