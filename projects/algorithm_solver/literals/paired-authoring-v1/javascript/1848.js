class Solution {
  getMinDistance(nums, target, start) {
    let best = nums.length;
    for (let index = 0; index < nums.length; index += 1) {
      if (nums[index] === target) {
        best = Math.min(best, Math.abs(index - start));
      }
    }
    return best;
  }
}
