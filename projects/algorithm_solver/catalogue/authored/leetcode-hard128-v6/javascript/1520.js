'use strict';

// 1520. Maximum Number of Non-Overlapping Substrings.
// Expand minimal closed character intervals, then select earliest finishes; O(26*n) time and O(26) auxiliary space, excluding output.

function solve(s) {
  const first = new Map(), last = new Map();
  for (let i = 0; i < s.length; i += 1) {
    if (!first.has(s[i])) first.set(s[i], i);
    last.set(s[i], i);
  }
  const intervals = [];
  for (const [char, start] of first) {
    let end = last.get(char), index = start;
    while (index <= end && first.get(s[index]) >= start) {
      end = Math.max(end, last.get(s[index]));
      index += 1;
    }
    if (index > end) intervals.push([end, start]);
  }
  intervals.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
  const answer = [];
  let previous = -1;
  for (const [end, start] of intervals) {
    if (start > previous) { answer.push(s.slice(start, end + 1)); previous = end; }
  }
  return answer;
}

const maxNumOfSubstrings = solve;
class Solution {
  maxNumOfSubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumOfSubstrings };
