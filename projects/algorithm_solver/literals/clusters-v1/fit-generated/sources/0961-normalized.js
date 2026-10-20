function firstRepeatedValue(values) {
  const seenValues = {};
  for (const value of values) {
    if (seenValues[value]) {
      return value;
    }
    seenValues[value] = true;
  }
  return null;
}
function solve(nums) {
  return firstRepeatedValue(nums);
}
