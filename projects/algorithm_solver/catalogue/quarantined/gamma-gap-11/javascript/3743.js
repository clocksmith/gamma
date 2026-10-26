'use strict';

// 3743. Maximize Cyclic Partition Score.
// O(n * min(k, n/2)) time and O(min(k, n/2)) auxiliary space; exact cyclic endpoint-pair dynamic programming.
function solve(nums, k) {
  const limit = Math.min(k, Math.floor(nums.length / 2));
  if (limit === 0) return 0;
  let answer = 0;
  // States: outside a pair, holding +value, holding -value. Matching the
  // boundary state permits one extremal pair to cross the cyclic seam.
  for (let initial = 0; initial < 3; initial += 1) {
    let state = Array.from({ length: 3 }, () => Array(limit + 1).fill(-Infinity));
    state[initial][0] = 0;
    for (const value of nums) {
      const following = state.map(values => values.slice());
      for (let count = 0; count <= limit; count += 1) {
        following[1][count] = Math.max(following[1][count], state[0][count] + value);
        following[2][count] = Math.max(following[2][count], state[0][count] - value);
        if (count < limit) {
          following[0][count + 1] = Math.max(following[0][count + 1], state[1][count] - value, state[2][count] + value);
        }
      }
      state = following;
    }
    for (const score of state[initial]) answer = Math.max(answer, score);
  }
  return answer;
}

const maxScore = solve;
class Solution {
  maxScore(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
