'use strict';

// 1630. Arithmetic Subarrays: check unique positions in the implied arithmetic progression.
// O(total queried length) expected time and O(longest query length) auxiliary space; inputs are read-only.
function solve(nums, l, r) {
  const answer = [];
  for (let query = 0; query < l.length; query += 1) {
    const left = l[query];
    const right = r[query];
    let low = nums[left];
    let high = nums[left];
    for (let index = left + 1; index <= right; index += 1) {
      low = Math.min(low, nums[index]);
      high = Math.max(high, nums[index]);
    }
    if (low === high) {
      answer.push(true);
      continue;
    }
    const gaps = right - left;
    if ((high - low) % gaps !== 0) {
      answer.push(false);
      continue;
    }
    const step = (high - low) / gaps;
    const seen = new Set();
    let valid = true;
    for (let index = left; index <= right; index += 1) {
      const value = nums[index];
      if ((value - low) % step !== 0 || seen.has(value)) {
        valid = false;
        break;
      }
      seen.add(value);
    }
    answer.push(valid);
  }
  return answer;
}

const checkArithmeticSubarrays = solve;
class Solution {
  checkArithmeticSubarrays(nums, l, r) { return solve(nums, l, r); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkArithmeticSubarrays };
