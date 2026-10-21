function firstRepeatedValue(values) {
  const seenValues = {};
  for (const value of values) {
    if (seenValues[value]) {
      return value;
    }
    seenValues[value] = true;
  }
  return null;
}
class Solution {
  repeatedNTimes(nums) {
    return firstRepeatedValue(nums);
  }
}
