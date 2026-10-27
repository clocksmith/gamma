/**
 * 3944. Minimum Operations to Make Array Modulo Alternating II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-array-modulo-alternating-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3944.Minimum%20Operations%20to%20Make%20Array%20Modulo%20Alternating%20II/README_EN.md
 * Complexity: O(n+k) time, O(k) auxiliary space.
 * Circular residue distances; two distinct targets. Inputs preserved. All totals safely bounded for n,k<=1e5; native name pending for II.
 */

function solve(nums, k) {
  const frequency = [new Int32Array(k), new Int32Array(k)];
  nums.forEach((value, index) => { frequency[index % 2][value % k] += 1; });
  function costs(counts) {
    const prefixCount = new Float64Array(2 * k + 1);
    const prefixWeight = new Float64Array(2 * k + 1);
    for (let index = 0; index < 2 * k; index += 1) {
      const count = counts[index % k];
      prefixCount[index + 1] = prefixCount[index] + count;
      prefixWeight[index + 1] = prefixWeight[index] + index * count;
    }
    const result = Array(k);
    for (let residue = 0; residue < k; residue += 1) {
      const middle = residue + Math.floor(k / 2) + 1;
      const end = residue + k;
      result[residue] = prefixWeight[middle] - prefixWeight[residue] - residue * (prefixCount[middle] - prefixCount[residue])
        + end * (prefixCount[end] - prefixCount[middle]) - (prefixWeight[end] - prefixWeight[middle]);
    }
    return result;
  }
  const even = costs(frequency[0]);
  const odd = costs(frequency[1]);
  let first = 0;
  for (let index = 1; index < k; index += 1) if (odd[index] < odd[first]) first = index;
  let second = Infinity;
  for (let index = 0; index < k; index += 1) if (index !== first) second = Math.min(second, odd[index]);
  let answer = Infinity;
  for (let index = 0; index < k; index += 1) answer = Math.min(answer, even[index] + (index === first ? second : odd[first]));
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
