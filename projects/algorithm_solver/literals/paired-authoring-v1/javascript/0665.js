class Solution {
  checkPossibility(nums) {
    if (nums.length < 2) {
      return true;
    }

    let changes = 0;
    let previous = nums[0];
    for (let index = 1; index < nums.length; index += 1) {
      const current = nums[index];
      if (current >= previous) {
        previous = current;
        continue;
      }
      changes += 1;
      if (changes > 1) {
        return false;
      }
      if (index === 1 || nums[index - 2] <= current) {
        previous = current;
      }
    }
    return true;
  }
}
