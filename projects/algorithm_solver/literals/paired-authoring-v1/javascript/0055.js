class Solution {
  canJump(nums) {
    let farthest = 0;
    for (let index = 0; index < nums.length; index += 1) {
      if (index > farthest) {
        return false;
      }
      farthest = Math.max(farthest, index + nums[index]);
      if (farthest >= nums.length - 1) {
        return true;
      }
    }
    return false;
  }
}
