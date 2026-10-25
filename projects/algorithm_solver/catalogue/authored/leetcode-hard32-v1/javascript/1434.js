'use strict';

// 1434. Number of Ways to Wear Different Hats to Each Other.
// O(40*n*2^n) time, O(2^n + 40*n) space; a fresh DP layer prevents reusing a hat.
function solve(hats) {
  const modulus = 1000000007;
  const people = Array.from({ length: 41 }, () => []);
  for (let person = 0; person < hats.length; person += 1) {
    for (const hat of hats[person]) people[hat].push(person);
  }
  const states = 1 << hats.length;
  let ways = new Float64Array(states);
  ways[0] = 1;
  for (let hat = 1; hat <= 40; hat += 1) {
    const following = ways.slice();
    for (let mask = 0; mask < states; mask += 1) {
      const count = ways[mask];
      if (count === 0) continue;
      for (const person of people[hat]) {
        const bit = 1 << person;
        if ((mask & bit) === 0) following[mask | bit] = (following[mask | bit] + count) % modulus;
      }
    }
    ways = following;
  }
  return ways[states - 1];
}

const numberWays = solve;
class Solution {
  numberWays(hats) { return solve(hats); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberWays };
