'use strict';

// 3776. Minimum Moves to Balance Circular Array.
// O(n) time and O(1) auxiliary space; consume nearest supplies for the sole possible deficit.
function solve(balance) {
  let total = 0;
  let negative = -1;
  for (let index = 0; index < balance.length; index += 1) {
    total += balance[index];
    if (balance[index] < 0) negative = index;
  }
  if (total < 0) return -1;
  if (negative < 0) return 0;
  let remaining = -balance[negative];
  let answer = 0;
  const n = balance.length;
  for (let distance = 1; distance <= Math.floor(n / 2); distance += 1) {
    const left = (negative - distance + n) % n;
    const right = (negative + distance) % n;
    const supply = balance[left] + (right === left ? 0 : balance[right]);
    const taken = Math.min(remaining, supply);
    answer += distance * taken;
    remaining -= taken;
    if (remaining === 0) return answer;
  }
  return -1;
}

const minMoves = solve;
class Solution {
  minMoves(balance) { return solve(balance); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMoves };
