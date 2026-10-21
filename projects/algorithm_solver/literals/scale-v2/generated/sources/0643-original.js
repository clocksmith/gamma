function maximumFixedWindowAverage(values, windowLength) {
  let windowSum = 0;
  for (let valueIndex = 0; valueIndex < windowLength; valueIndex += 1) {
    windowSum += values[valueIndex];
  }
  let maximumSum = windowSum;
  for (let valueIndex = windowLength; valueIndex < values.length; valueIndex += 1) {
    windowSum += values[valueIndex] - values[valueIndex - windowLength];
    if (windowSum > maximumSum) {
      maximumSum = windowSum;
    }
  }
  return maximumSum / windowLength;
}
class Solution {
  findMaxAverage(nums, k) {
    return maximumFixedWindowAverage(nums, k);
  }
}
