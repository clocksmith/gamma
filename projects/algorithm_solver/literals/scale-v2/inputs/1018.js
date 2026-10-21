function prefixDivisibilityByFive(values) {
  const resultValues = [];
  let remainderValue = 0;
  for (const value of values) {
    remainderValue = ((remainderValue * 2 | value) % 5 + 5) % 5;
    resultValues.push(remainderValue === 0);
  }
  return resultValues;
}
class Solution {
  prefixesDivBy5(nums) {
    return prefixDivisibilityByFive(nums);
  }
}
