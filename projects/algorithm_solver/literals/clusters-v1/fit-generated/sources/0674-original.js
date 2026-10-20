function longestIncreasingRun(values) {
  let currentLength = 1;
  let longestLength = 1;
  for (let valueIndex = 1; valueIndex < values.length; valueIndex += 1) {
    if (values[valueIndex - 1] < values[valueIndex]) {
      currentLength += 1;
      if (currentLength > longestLength) {
        longestLength = currentLength;
      }
    } else {
      currentLength = 1;
    }
  }
  return longestLength;
}
class Solution {
  findLengthOfLCIS(nums) {
    return longestIncreasingRun(nums);
  }
}
