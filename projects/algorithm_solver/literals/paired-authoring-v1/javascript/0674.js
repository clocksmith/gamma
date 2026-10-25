class Solution {
  findLengthOfLCIS(nums) {
    let longest = 0;
    let length = 0;
    for (let index = 0; index < nums.length; index += 1) {
      const value = nums[index];
      if (index > 0 && nums[index - 1] < value) {
        length += 1;
      } else {
        length = 1;
      }
      longest = Math.max(longest, length);
    }
    return longest;
  }
}
