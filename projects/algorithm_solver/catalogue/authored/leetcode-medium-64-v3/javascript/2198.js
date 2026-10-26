'use strict';

// 2198. Number of Single Divisor Triplets: enumerate value multisets and count all distinct-index orderings.
// O(n + u^3) time and O(u) auxiliary space for u <= 100 distinct values; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const values = [...counts.keys()].sort((left, right) => left - right);
  let answer = 0;
  for (let first = 0; first < values.length; first += 1) {
    const a = values[first];
    for (let second = first; second < values.length; second += 1) {
      const b = values[second];
      for (let third = second; third < values.length; third += 1) {
        const c = values[third];
        const total = a + b + c;
        const divisors = Number(total % a === 0) + Number(total % b === 0) + Number(total % c === 0);
        if (divisors !== 1) continue;
        let choices;
        if (a === b) choices = counts.get(a) * (counts.get(a) - 1) / 2 * counts.get(c);
        else if (b === c) choices = counts.get(a) * (counts.get(b) * (counts.get(b) - 1) / 2);
        else choices = counts.get(a) * counts.get(b) * counts.get(c);
        answer += 6 * choices;
      }
    }
  }
  return answer;
}

const singleDivisorTriplet = solve;
class Solution {
  singleDivisorTriplet(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, singleDivisorTriplet };
