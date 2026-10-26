'use strict';

// 3273. Minimum Amount of Damage Dealt to Bob.
// Order enemies by processing-time/damage ratio using integer cross-products; O(n log n) time and O(n) space. Inputs are preserved. Return Number when safe, otherwise exact BigInt.

function solve(power, damage, health) {
  const jobs = health.map((value, index) => [Math.ceil(value / power), damage[index], index]);
  jobs.sort((a, b) => a[0] * b[1] - b[0] * a[1] || a[2] - b[2]);
  let remaining = damage.reduce((sum, value) => sum + value, 0), answer = 0n;
  for (const [duration, rate] of jobs) {
    answer += BigInt(duration) * BigInt(remaining);
    remaining -= rate;
  }
  return answer <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(answer) : answer;
}

const minDamage = solve;
class Solution {
  minDamage(power, damage, health) { return solve(power, damage, health); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDamage };
