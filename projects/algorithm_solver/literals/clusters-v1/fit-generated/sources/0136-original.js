function singleUnpairedValue(values) {
  let unpairedValue = 0;
  for (const value of values) {
    unpairedValue ^= value;
  }
  return unpairedValue;
}
class Solution {
  singleNumber(nums) {
    return singleUnpairedValue(nums);
  }
}
