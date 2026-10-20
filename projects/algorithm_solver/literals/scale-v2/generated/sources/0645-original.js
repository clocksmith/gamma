function findSetMismatch(values) {
  const valueCount = values.length;
  const expectedSum = valueCount * (valueCount + 1) / 2;
  let totalSum = 0;
  let uniqueSum = 0;
  const seenValues = {};
  for (const value of values) {
    totalSum += value;
    if (!seenValues[value]) {
      seenValues[value] = true;
      uniqueSum += value;
    }
  }
  return [totalSum - uniqueSum, expectedSum - uniqueSum];
}
class Solution {
  findErrorNums(nums) {
    return findSetMismatch(nums);
  }
}
