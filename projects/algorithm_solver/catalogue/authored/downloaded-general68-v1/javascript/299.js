'use strict';

// 299. Bulls and Cows (Medium).
// Specification: https://leetcode.com/problems/bulls-and-cows/description/
function solve(secret, guess) {
  let bulls = 0;
  const secretCounts = new Array(10).fill(0);
  const guessCounts = new Array(10).fill(0);
  for (let i = 0; i < secret.length; i++) {
    if (secret[i] === guess[i]) bulls++;
    else { secretCounts[Number(secret[i])]++; guessCounts[Number(guess[i])]++; }
  }
  let cows = 0;
  for (let digit = 0; digit < 10; digit++) cows += Math.min(secretCounts[digit], guessCounts[digit]);
  return `${bulls}A${cows}B`;
}
const getHint = solve;
class Solution { getHint(secret, guess) { return solve(secret, guess); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getHint };
