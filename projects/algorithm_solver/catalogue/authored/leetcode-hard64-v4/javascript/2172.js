'use strict';

// 2172. Maximum AND Sum of Array. Base-three slot-occupancy DP; O(S*3^S) time and O(3^S) space. Inputs are preserved.

function solve(nums, numSlots) {
  const powers = Array.from({ length: numSlots }, (_, slot) => 3 ** slot);
  const states = 3 ** numSlots;
  const best = new Int32Array(states).fill(-1);
  const occupied = new Uint8Array(states);
  best[0] = 0;
  for (let state = 1; state < states; state += 1) occupied[state] = occupied[Math.floor(state / 3)] + state % 3;
  let answer = 0;
  for (let state = 0; state < states; state += 1) {
    if (best[state] < 0) continue;
    const count = occupied[state];
    if (count === nums.length) {
      answer = Math.max(answer, best[state]);
      continue;
    }
    let digits = state;
    for (let slot = 0; slot < numSlots; slot += 1) {
      if (digits % 3 < 2) {
        const following = state + powers[slot];
        best[following] = Math.max(best[following], best[state] + (nums[count] & (slot + 1)));
      }
      digits = Math.floor(digits / 3);
    }
  }
  return answer;
}

const maximumANDSum = solve;
class Solution {
  maximumANDSum(nums, numSlots) { return solve(nums, numSlots); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumANDSum };
