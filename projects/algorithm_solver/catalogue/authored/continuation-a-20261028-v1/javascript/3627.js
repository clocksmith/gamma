function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let answer = 0;
  for (let group = 0; group < nums.length / 3; group++) answer += ordered[nums.length - 2 - 2 * group];
  return answer;
}

var maximumMedianSum = solve;
module.exports = solve;
