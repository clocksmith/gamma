'use strict';

// 3045. Count Prefix and Suffix Pairs II.
// Trie of paired forward/reverse letters counts earlier complete words; O(total characters) expected time and space. Inputs are preserved.

function solve(words) {
  const children = [new Map()], terminal = [0];
  let answer = 0;
  for (const word of words) {
    let state = 0;
    for (let index = 0; index < word.length; index += 1) {
      const pair = (word.charCodeAt(index) - 97) * 26 + word.charCodeAt(word.length - 1 - index) - 97;
      if (!children[state].has(pair)) { children[state].set(pair, children.length); children.push(new Map()); terminal.push(0); }
      state = children[state].get(pair); answer += terminal[state];
    }
    terminal[state] += 1;
  }
  return answer;
}

const countPrefixSuffixPairs = solve;
class Solution {
  countPrefixSuffixPairs(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPrefixSuffixPairs };
