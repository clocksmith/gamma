function solve(nums, k) {
  const ordered = nums.slice().sort((a, b) => a - b);
  let left = 0, best = 0;
  for (let right = 0; right < ordered.length; right++) {
    while (ordered[right] > ordered[left] * k) left++;
    best = Math.max(best, right - left + 1);
  }
  return nums.length - best;
}

var minRemoval = solve;
module.exports = solve;
