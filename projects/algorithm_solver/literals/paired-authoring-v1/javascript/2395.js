class Solution {
  findSubarrays(nums) {
    const seen = new Set();
    for (let index = 1; index < nums.length; index += 1) {
      const total = nums[index - 1] + nums[index];
      if (seen.has(total)) {
        return true;
      }
      seen.add(total);
    }
    return false;
  }
}
