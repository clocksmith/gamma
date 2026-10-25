function solve(nums) {
  // O(n) time and output space; return a fresh array.
  const length = nums.length;
  const answer = new Array(2 * length);
  for (let index = 0; index < length; index++) {
    answer[index] = nums[index];
    answer[length + index] = nums[length - index - 1];
  }
  return answer;
}
