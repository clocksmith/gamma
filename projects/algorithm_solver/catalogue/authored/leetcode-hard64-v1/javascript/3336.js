'use strict';

// 3336. Find the Number of Subsequences With Equal GCD: assign each index to neither or exactly one of two gcd states.
// O(n*M^2 + M^2 log M) time and O(M^2) auxiliary space. Inputs are preserved.
function solve(nums) {
  const modulus = 1000000007;
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const size = maximum + 1;
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  const common = Array.from({ length: size }, (_, first) =>
    Int32Array.from({ length: size }, (_, second) => gcd(first, second)));
  let ways = new Float64Array(size * size);
  ways[0] = 1;
  for (const value of nums) {
    const following = ways.slice();
    const transform = common[value];
    for (let first = 0; first < size; first += 1) {
      const row = first * size;
      const nextRow = transform[first] * size;
      for (let second = 0; second < size; second += 1) {
        const count = ways[row + second];
        if (count === 0) continue;
        const leftIndex = nextRow + second;
        const rightIndex = row + transform[second];
        following[leftIndex] = (following[leftIndex] + count) % modulus;
        following[rightIndex] = (following[rightIndex] + count) % modulus;
      }
    }
    ways = following;
  }
  let answer = 0;
  for (let value = 1; value < size; value += 1) answer = (answer + ways[value * size + value]) % modulus;
  return answer;
}

const subsequencePairCount = solve;
class Solution {
  subsequencePairCount(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsequencePairCount };
