function singleUnpairedValue(values) {
  let unpairedValue = 0;
  for (const value of values) {
    unpairedValue ^= value;
  }
  return unpairedValue;
}
function solve(nums) {
  return singleUnpairedValue(nums);
}
