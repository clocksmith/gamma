'use strict';

// 3272. Find the Count of Good Integers.
// Enumerate divisible palindromes, deduplicate digit multisets, and count permutations excluding leading zero; O(n*10^ceil(n/2)) time and space proportional to distinct multisets. Inputs are preserved.

function solve(n, k) {
  const half = Math.ceil(n / 2), seen = new Set(), factorial = [1];
  for (let value = 1; value <= n; value += 1) factorial.push(factorial[value - 1] * value);
  let answer = 0;
  for (let prefix = 10 ** (half - 1); prefix < 10 ** half; prefix += 1) {
    const left = String(prefix), reflected = n % 2 ? left.slice(0, -1) : left;
    const text = left + reflected.split('').reverse().join('');
    if (Number(text) % k !== 0) continue;
    const counts = Array(10).fill(0);
    for (const character of text) counts[Number(character)] += 1;
    const identity = counts.join(',');
    if (seen.has(identity)) continue;
    seen.add(identity);
    let denominator = 1;
    for (const count of counts) denominator *= factorial[count];
    answer += (n - counts[0]) * factorial[n - 1] / denominator;
  }
  return answer;
}

const countGoodIntegers = solve;
class Solution {
  countGoodIntegers(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodIntegers };
