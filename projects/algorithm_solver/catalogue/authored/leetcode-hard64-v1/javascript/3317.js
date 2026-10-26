'use strict';

// 3317. Find the Number of Possible Ways for an Event: count assignments by the number of occupied labeled stages.
// O(n*min(n,x)) time and O(min(n,x)) auxiliary space. Inputs are preserved.
function solve(n, x, y) {
  const modulus = 1000000007;
  const size = Math.min(n, x);
  const ways = new Float64Array(size + 1);
  ways[0] = 1;
  for (let performer = 1; performer <= n; performer += 1) {
    for (let occupied = Math.min(performer, size); occupied > 0; occupied -= 1) {
      ways[occupied] = (occupied * ways[occupied]
        + (x - occupied + 1) * ways[occupied - 1]) % modulus;
    }
    ways[0] = 0;
  }
  let answer = 0n;
  let scores = 1n;
  const bigModulus = BigInt(modulus);
  for (let occupied = 1; occupied <= size; occupied += 1) {
    scores = scores * BigInt(y) % bigModulus;
    answer = (answer + BigInt(ways[occupied]) * scores) % bigModulus;
  }
  return Number(answer);
}

const numberOfWays = solve;
class Solution {
  numberOfWays(n, x, y) { return solve(n, x, y); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
