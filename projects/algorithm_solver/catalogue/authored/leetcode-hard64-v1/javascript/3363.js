'use strict';

// 3363. Find the Maximum Number of Fruits Collected: forced diagonal plus independent optimal paths above and below it.
// O(n^2) time and O(n) auxiliary space for nonnegative fruit counts. Inputs are preserved.
function solve(fruits) {
  const n = fruits.length;
  if (n === 1) return fruits[0][0];
  let answer = 0;
  for (let index = 0; index < n; index += 1) answer += fruits[index][index];
  function side(transposed) {
    let previous = new Float64Array(n).fill(-Infinity);
    previous[n - 1] = transposed ? fruits[n - 1][0] : fruits[0][n - 1];
    for (let step = 1; step < n - 1; step += 1) {
      const following = new Float64Array(n).fill(-Infinity);
      for (let position = step + 1; position < n; position += 1) {
        let best = previous[position];
        if (position > 0) best = Math.max(best, previous[position - 1]);
        if (position + 1 < n) best = Math.max(best, previous[position + 1]);
        following[position] = best + (transposed ? fruits[position][step] : fruits[step][position]);
      }
      previous = following;
    }
    return previous[n - 1];
  }
  return answer + side(false) + side(true);
}

const maxCollectedFruits = solve;
class Solution {
  maxCollectedFruits(fruits) { return solve(fruits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCollectedFruits };
