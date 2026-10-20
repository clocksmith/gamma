function findPivotIndex(values) {
  let rightSum = 0;
  for (const value of values) {
    rightSum += value;
  }
  let leftSum = 0;
  for (let valueIndex = 0; valueIndex < values.length; valueIndex += 1) {
    rightSum -= values[valueIndex];
    if (leftSum === rightSum) {
      return valueIndex;
    }
    leftSum += values[valueIndex];
  }
  return -1;
}
class Solution {
  pivotIndex(nums) {
    return findPivotIndex(nums);
  }
}
