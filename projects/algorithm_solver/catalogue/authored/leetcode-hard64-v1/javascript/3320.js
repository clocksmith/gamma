'use strict';

// 3320. Count the Number of Winning Sequences: rolling dynamic programming over score difference and last move.
// O(n^2) time and O(n) auxiliary space. Inputs are preserved.
function solve(s) {
  const modulus = 1000000007;
  const n = s.length;
  const width = 2 * n + 1;
  const symbols = { F: 0, W: 1, E: 2 };
  let ways = Array.from({ length: 3 }, () => new Float64Array(width));
  const first = symbols[s[0]];
  for (let move = 0; move < 3; move += 1) {
    const difference = (move - first + 3) % 3;
    const delta = difference === 0 ? 0 : difference === 1 ? 1 : -1;
    ways[move][n + delta] = 1;
  }
  for (let round = 1; round < n; round += 1) {
    const opponent = symbols[s[round]];
    const following = Array.from({ length: 3 }, () => new Float64Array(width));
    for (let move = 0; move < 3; move += 1) {
      const difference = (move - opponent + 3) % 3;
      const delta = difference === 0 ? 0 : difference === 1 ? 1 : -1;
      for (let previous = 0; previous < 3; previous += 1) {
        if (previous === move) continue;
        for (let score = n - round; score <= n + round; score += 1) {
          following[move][score + delta] = (following[move][score + delta] + ways[previous][score]) % modulus;
        }
      }
    }
    ways = following;
  }
  let answer = 0;
  for (const row of ways) {
    for (let score = n + 1; score < width; score += 1) answer = (answer + row[score]) % modulus;
  }
  return answer;
}

const countWinningSequences = solve;
class Solution {
  countWinningSequences(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countWinningSequences };
