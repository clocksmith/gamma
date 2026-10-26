'use strict';

// 401. Binary Watch (Easy).
// Specification: https://leetcode.com/problems/binary-watch/description/
// O(1) bounded enumeration of 720 times; return fresh strings in chronological order.
function solve(turnedOn) {
  function bitCount(value) {
    let count = 0;
    while (value > 0) {
      value &= value - 1;
      count++;
    }
    return count;
  }
  const result = [];
  for (let hour = 0; hour < 12; hour++) {
    for (let minute = 0; minute < 60; minute++) {
      if (bitCount(hour) + bitCount(minute) === turnedOn) {
        result.push(String(hour) + ':' + String(minute).padStart(2, '0'));
      }
    }
  }
  return result;
}

const readBinaryWatch = solve;
class Solution {
  readBinaryWatch(turnedOn) { return solve(turnedOn); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, readBinaryWatch };
