'use strict';

// 3149. Find the Minimum Cost Array Permutation: subset dynamic programming and lexicographic reconstruction.
// O(n^2 * 2^n) time and O(n * 2^n) auxiliary space. Inputs are preserved.
function solve(nums) {
  const n = nums.length;
  const full = (1 << n) - 1;
  const memo = new Int32Array((1 << n) * n).fill(-1);
  function best(mask, last) {
    if (mask === full) return Math.abs(last - nums[0]);
    const key = mask * n + last;
    if (memo[key] !== -1) return memo[key];
    let value = n * n;
    for (let following = 1; following < n; following += 1) {
      if ((mask & (1 << following)) === 0) {
        value = Math.min(value, Math.abs(last - nums[following]) + best(mask | (1 << following), following));
      }
    }
    memo[key] = value;
    return value;
  }
  const answer = [0];
  let mask = 1;
  let last = 0;
  while (mask !== full) {
    const remaining = best(mask, last);
    for (let following = 1; following < n; following += 1) {
      if (mask & (1 << following)) continue;
      const candidate = Math.abs(last - nums[following]) + best(mask | (1 << following), following);
      if (candidate === remaining) {
        answer.push(following);
        mask |= 1 << following;
        last = following;
        break;
      }
    }
  }
  return answer;
}

const findPermutation = solve;
class Solution {
  findPermutation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPermutation };
