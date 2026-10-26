'use strict';

// 1259. Handshakes That Do Not Cross.
// Catalan interval decomposition; O(n^2) time and O(n) space for n pairs.

const MOD = 1000000007;
// Split multiplication keeps every intermediate integer below 2^53.
function multiplyMod(a, b) {
  return (a * (b % 32768) + ((a * Math.floor(b / 32768)) % MOD) * 32768) % MOD;
}
function powerMod(base, exponent) {
  let result = 1;
  while (exponent > 0) {
    if (exponent % 2 === 1) result = multiplyMod(result, base);
    base = multiplyMod(base, base);
    exponent = Math.floor(exponent / 2);
  }
  return result;
}

function solve(numPeople) {
  const pairs = numPeople / 2;
  const ways = Array(pairs + 1).fill(0);
  ways[0] = 1;
  for (let size = 1; size <= pairs; size += 1) {
    for (let left = 0; left < size; left += 1) ways[size] = (ways[size] + multiplyMod(ways[left], ways[size - left - 1])) % MOD;
  }
  return ways[pairs];
}

const numberOfWays = solve;
class Solution {
  numberOfWays(numPeople) { return solve(numPeople); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfWays };
