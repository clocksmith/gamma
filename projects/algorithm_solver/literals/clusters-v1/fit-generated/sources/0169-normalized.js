function majorityValue(values) {
  let candidateValue = 0;
  let balanceCount = 0;
  for (const value of values) {
    if (balanceCount === 0) {
      candidateValue = value;
    }
    if (value === candidateValue) {
      balanceCount += 1;
    } else {
      balanceCount -= 1;
    }
  }
  return candidateValue;
}
function solve(nums) {
  return majorityValue(nums);
}
