'use strict';

// 3224. Minimum Array Changes to Make Differences Equal: sweep the zero-change and one-change difference ranges of mirrored pairs.
// O(n + k) time and O(k) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const changes = new Int32Array(k + 2);
  const pairs = Math.floor(nums.length / 2);
  for (let index = 0; index < pairs; index += 1) {
    const left = nums[index];
    const right = nums[nums.length - 1 - index];
    const difference = Math.abs(left - right);
    const oneChangeLimit = Math.max(left, right, k - left, k - right);
    changes[0] -= 1;
    changes[oneChangeLimit + 1] += 1;
    changes[difference] -= 1;
    changes[difference + 1] += 1;
  }
  let running = 2 * pairs;
  let best = running;
  for (let difference = 0; difference <= k; difference += 1) {
    running += changes[difference];
    best = Math.min(best, running);
  }
  return best;
}

const minChanges = solve;
class Solution {
  minChanges(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minChanges };
