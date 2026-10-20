function smallestFlexibleRange(values, adjustment) {
  let minimumValue = values[0];
  let maximumValue = values[0];
  for (const value of values) {
    minimumValue = Math.min(minimumValue, value);
    maximumValue = Math.max(maximumValue, value);
  }
  return Math.max(0, maximumValue - minimumValue - adjustment * 2);
}
function solve(nums, k) {
  return smallestFlexibleRange(nums, k);
}
