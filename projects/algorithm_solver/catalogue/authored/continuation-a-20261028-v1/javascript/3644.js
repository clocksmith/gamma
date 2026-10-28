function solve(nums) {
  let answer = null;
  for (let i = 0; i < nums.length; i++) if (nums[i] !== i) answer = answer === null ? nums[i] : answer & nums[i];
  return answer === null ? 0 : answer;
}

var sortPermutation = solve;
module.exports = solve;
