'use strict';

// 809. Expressive Words: match letter runs against the allowed stretched groups.
// O(|s| + sum(|word|)) time and O(|s|) auxiliary space; inputs are read-only.
function solve(s, words) {
  const groups = [];
  let index = 0;
  while (index < s.length) {
    let end = index + 1;
    while (end < s.length && s[end] === s[index]) end += 1;
    groups.push([s[index], end - index]);
    index = end;
  }
  let answer = 0;
  for (const word of words) {
    let position = 0;
    let valid = true;
    for (const [character, required] of groups) {
      if (position === word.length || word[position] !== character) {
        valid = false;
        break;
      }
      let end = position + 1;
      while (end < word.length && word[end] === character) end += 1;
      const actual = end - position;
      if (actual > required || (actual !== required && required < 3)) {
        valid = false;
        break;
      }
      position = end;
    }
    if (valid && position === word.length) answer += 1;
  }
  return answer;
}

const expressiveWords = solve;
class Solution {
  expressiveWords(s, words) { return solve(s, words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, expressiveWords };
