function solve(nums) {
  // O(n) time and O(1) auxiliary space; count swaps without mutating nums.
  let nonzero = 0;
  for (const value of nums) {
    if (value !== 0) nonzero++;
  }
  let answer = 0;
  for (let index = 0; index < nonzero; index++) {
    if (nums[index] === 0) answer++;
  }
  return answer;
}
