function minimumDecimalDigitEvenness(values) {
  let minimumValue = Math.min(...values);
  let digitTotal = 0;
  while (minimumValue) {
    digitTotal += (minimumValue % 10 + 10) % 10;
    minimumValue = Math.floor(minimumValue / 10);
  }
  return digitTotal & 1 ^ 1;
}
class Solution {
  sumOfDigits(nums) {
    return minimumDecimalDigitEvenness(nums);
  }
}
