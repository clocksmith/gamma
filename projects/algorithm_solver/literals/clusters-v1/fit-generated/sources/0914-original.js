function greatestCommonDivisor(leftValue, rightValue) {
  leftValue = Math.abs(leftValue);
  rightValue = Math.abs(rightValue);
  while (rightValue !== 0) {
    const remainder = leftValue % rightValue;
    leftValue = rightValue;
    rightValue = remainder;
  }
  return leftValue;
}
function canGroupCards(values) {
  const countsByValue = {};
  for (const value of values) {
    countsByValue[value] = (countsByValue[value] || 0) + 1;
  }
  let commonCount = 0;
  for (const value in countsByValue) {
    const frequency = countsByValue[value];
    commonCount = greatestCommonDivisor(commonCount, frequency);
  }
  return commonCount >= 2;
}
class Solution {
  hasGroupsSizeX(deck) {
    return canGroupCards(deck);
  }
}
