class Solution {
  movesToMakeZigzag(nums) {
    const costs = [0, 0];
    for (let index = 0; index < nums.length; index += 1) {
      const value = nums[index];
      let decrease = 0;
      if (index > 0) {
        decrease = Math.max(decrease, value - nums[index - 1] + 1);
      }
      if (index + 1 < nums.length) {
        decrease = Math.max(decrease, value - nums[index + 1] + 1);
      }
      costs[index % 2] += decrease;
    }
    return Math.min(costs[0], costs[1]);
  }
}
