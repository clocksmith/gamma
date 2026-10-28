'use strict';

// 953. Verifying an Alien Dictionary (Easy).
// Specification: https://leetcode.com/problems/verifying-an-alien-dictionary/description/
function solve(words, order) {
  const rank = new Map();
  for (let index = 0; index < order.length; index++) rank.set(order[index], index);
  for (let index = 1; index < words.length; index++) {
    const previous = words[index - 1];
    const current = words[index];
    let compared = false;
    for (let position = 0; position < Math.min(previous.length, current.length); position++) {
      if (previous[position] !== current[position]) {
        if (rank.get(previous[position]) > rank.get(current[position])) return false;
        compared = true;
        break;
      }
    }
    if (!compared && previous.length > current.length) return false;
  }
  return true;
}

const isAlienSorted = solve;
class Solution {
  isAlienSorted(words, order) { return solve(words, order); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isAlienSorted };
