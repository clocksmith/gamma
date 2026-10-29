// 315 — Count of Smaller Numbers After Self. Original implementation; authored candidate, not independently qualified.
function solve(nums) {
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const rank = new Map(values.map((v, i) => [v, i + 1]));
  const bit = Array(values.length + 1).fill(0), result = Array(nums.length).fill(0);
  for (let i = nums.length - 1; i >= 0; i--) {
    const r = rank.get(nums[i]);
    for (let j = r - 1; j > 0; j -= j & -j) result[i] += bit[j];
    for (let j = r; j < bit.length; j += j & -j) bit[j]++;
  }
  return result;
}

module.exports = { solve, countSmaller: solve };
