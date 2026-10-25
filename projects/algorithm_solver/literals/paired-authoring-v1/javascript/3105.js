class Solution {
  longestMonotonicSubarray(nums) {
    if (nums.length === 0) {
      return 0;
    }
    let increasing = 1;
    let decreasing = 1;
    let best = 1;
    for (let index = 1; index < nums.length; index += 1) {
      if (nums[index] > nums[index - 1]) {
        increasing += 1;
      } else {
        increasing = 1;
      }
      if (nums[index] < nums[index - 1]) {
        decreasing += 1;
      } else {
        decreasing = 1;
      }
      best = Math.max(best, increasing, decreasing);
    }
    return best;
  }
}
