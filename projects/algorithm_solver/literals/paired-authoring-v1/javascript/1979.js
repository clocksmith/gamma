class Solution {
  findGCD(nums) {
    let first = nums[0];
    let second = nums[0];
    for (const value of nums) {
      first = Math.min(first, value);
      second = Math.max(second, value);
    }
    while (second !== 0) {
      [first, second] = [second, first % second];
    }
    return first;
  }
}
