'use strict';

// 3386. Button with Longest Push Time (Easy).
// Specification: https://leetcode.com/problems/button-with-longest-push-time/description/
// O(n) time, O(1) auxiliary space; equal durations favor the smallest button index.
function solve(events) {
  let previousTime = 0;
  let longest = -1;
  let bestButton = events[0][0];
  for (const [button, time] of events) {
    const duration = time - previousTime;
    if (duration > longest || (duration === longest && button < bestButton)) {
      longest = duration;
      bestButton = button;
    }
    previousTime = time;
  }
  return bestButton;
}

const buttonWithLongestTime = solve;
class Solution {
  buttonWithLongestTime(events) { return solve(events); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, buttonWithLongestTime };
