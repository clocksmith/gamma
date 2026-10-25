class Solution {
  check(nums) {
    let descents = 0;
    for (let index = 0; index < nums.length; index += 1) {
      if (nums[index] > nums[(index + 1) % nums.length]) {
        descents += 1;
        if (descents > 1) {
          return false;
        }
      }
    }
    return true;
  }
}
