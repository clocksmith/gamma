function maximizeNegatedSum(values, remainingCount) {
  const countsByValue = {};
  const uniqueValues = [];
  for (const value of values) {
    if (!(value in countsByValue)) {
      uniqueValues.push(value);
    }
    countsByValue[value] = (countsByValue[value] || 0) + 1;
  }
  for (let value = -100; value < 0; value += 1) {
    if (countsByValue[value]) {
      const changedCount = Math.min(countsByValue[value], remainingCount);
      countsByValue[value] -= changedCount;
      if (!(-value in countsByValue)) {
        uniqueValues.push(-value);
      }
      countsByValue[-value] = (countsByValue[-value] || 0) + changedCount;
      remainingCount -= changedCount;
      if (remainingCount === 0) {
        break;
      }
    }
  }
  if (remainingCount % 2 !== 0 && (countsByValue[0] || 0) === 0) {
    for (let value = 1; value <= 100; value += 1) {
      if (countsByValue[value]) {
        countsByValue[value] -= 1;
        if (!(-value in countsByValue)) {
          uniqueValues.push(-value);
        }
        countsByValue[-value] = (countsByValue[-value] || 0) + 1;
        break;
      }
    }
  }
  let resultTotal = 0;
  for (const value of uniqueValues) {
    resultTotal += value * countsByValue[value];
  }
  return resultTotal;
}
class Solution {
  largestSumAfterKNegations(nums, k) {
    return maximizeNegatedSum(nums, k);
  }
}
