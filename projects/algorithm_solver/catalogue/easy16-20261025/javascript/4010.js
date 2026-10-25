function solve(nums) {
  // O(n^2 log M) time and O(1) space. Products <= 10^10 are exact Numbers.
  function gcd(left, right) {
    while (right !== 0) {
      const remainder = left % right;
      left = right;
      right = remainder;
    }
    return left;
  }
  let answer = 0;
  for (let left = 0; left < nums.length; left++) {
    for (let right = left + 1; right < nums.length; right++) {
      const divisor = gcd(nums[left], nums[right]);
      const strength = (nums[left] / divisor) * (nums[right] / divisor);
      answer = Math.max(answer, strength);
    }
  }
  return answer;
}
