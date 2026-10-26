'use strict';

// 3333. Find the Original Typed String II: subtract short originals using bounded-choice prefix-sum dynamic programming.
// O(n + k^2) time and O(n + k) auxiliary space. Inputs are preserved.
function solve(word, k) {
  const modulus = 1000000007;
  const runs = [];
  let length = 0;
  let previous = '';
  for (const character of word) {
    if (character === previous) {
      length += 1;
    } else {
      if (length > 0) runs.push(length);
      length = 1;
      previous = character;
    }
  }
  runs.push(length);
  let total = 1;
  for (const run of runs) total = total * run % modulus;
  if (runs.length >= k) return total;
  let ways = new Float64Array(k);
  ways[0] = 1;
  for (const run of runs) {
    const following = new Float64Array(k);
    let window = 0;
    for (let size = 1; size < k; size += 1) {
      window += ways[size - 1];
      if (size - run - 1 >= 0) window -= ways[size - run - 1];
      window = (window + modulus) % modulus;
      following[size] = window;
    }
    ways = following;
  }
  let invalid = 0;
  for (const count of ways) invalid = (invalid + count) % modulus;
  return (total - invalid + modulus) % modulus;
}

const possibleStringCount = solve;
class Solution {
  possibleStringCount(word, k) { return solve(word, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, possibleStringCount };
