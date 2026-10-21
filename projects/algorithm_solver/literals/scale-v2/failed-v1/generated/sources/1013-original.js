function hasThreeEqualParts(values) {
  let totalValue = 0;
  for (const value of values) {
    totalValue += value;
  }
  if (totalValue % 3 !== 0) {
    return false;
  }
  const targetValue = totalValue / 3;
  let partCount = 0;
  let runningTotal = 0;
  for (const value of values) {
    runningTotal += value;
    if (runningTotal === targetValue) {
      partCount += 1;
      runningTotal = 0;
    }
  }
  return partCount >= 3;
}
class Solution {
  canThreePartsEqualSum(arr) {
    return hasThreeEqualParts(arr);
  }
}
