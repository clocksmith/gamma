function countIntegerValues(values) {
  const countsByValue = {};
  for (const value of values) {
    countsByValue[value] = (countsByValue[value] || 0) + 1;
  }
  return countsByValue;
}
function longestHarmoniousLength(values) {
  const countsByValue = countIntegerValues(values);
  let bestLength = 0;
  for (const value of values) {
    const adjacentCount = countsByValue[value + 1] || 0;
    if (adjacentCount > 0) {
      const candidateLength = countsByValue[value] + adjacentCount;
      if (candidateLength > bestLength) {
        bestLength = candidateLength;
      }
    }
  }
  return bestLength;
}
class Solution {
  findLHS(nums) {
    return longestHarmoniousLength(nums);
  }
}
