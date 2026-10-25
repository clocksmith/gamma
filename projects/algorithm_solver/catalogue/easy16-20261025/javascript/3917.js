function solve(nums) {
  // O(n) time, O(n) output space, O(1) auxiliary space.
  const counts = [0, 0];
  const answer = new Array(nums.length);
  for (let index = nums.length - 1; index >= 0; index--) {
    const parity = nums[index] % 2;
    answer[index] = counts[1 - parity];
    counts[parity]++;
  }
  return answer;
}
