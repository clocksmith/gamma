'use strict';

// 3455. Shortest Matching Substring: KMP occurrence lists joined with monotone pointers.
// O(|s| + |p|) time and O(|s| + |p|) auxiliary space. Inputs are preserved.
function solve(s, p) {
  const parts = p.split('*');
  function occurrences(pattern) {
    if (pattern.length === 0) return Array.from({ length: s.length + 1 }, (_, index) => index);
    const failure = new Int32Array(pattern.length);
    let matched = 0;
    for (let index = 1; index < pattern.length; index += 1) {
      while (matched > 0 && pattern[index] !== pattern[matched]) matched = failure[matched - 1];
      if (pattern[index] === pattern[matched]) matched += 1;
      failure[index] = matched;
    }
    const result = [];
    matched = 0;
    for (let index = 0; index < s.length; index += 1) {
      while (matched > 0 && s[index] !== pattern[matched]) matched = failure[matched - 1];
      if (s[index] === pattern[matched]) matched += 1;
      if (matched === pattern.length) {
        result.push(index - pattern.length + 1);
        matched = failure[matched - 1];
      }
    }
    return result;
  }
  const [first, second, third] = parts.map(occurrences);
  let secondIndex = 0;
  let thirdIndex = 0;
  let answer = s.length + 1;
  for (const start of first) {
    while (secondIndex < second.length && second[secondIndex] < start + parts[0].length) secondIndex += 1;
    if (secondIndex === second.length) break;
    const middleEnd = second[secondIndex] + parts[1].length;
    while (thirdIndex < third.length && third[thirdIndex] < middleEnd) thirdIndex += 1;
    if (thirdIndex === third.length) break;
    answer = Math.min(answer, third[thirdIndex] + parts[2].length - start);
  }
  return answer <= s.length ? answer : -1;
}

const shortestMatchingSubstring = solve;
class Solution {
  shortestMatchingSubstring(s, p) { return solve(s, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestMatchingSubstring };
