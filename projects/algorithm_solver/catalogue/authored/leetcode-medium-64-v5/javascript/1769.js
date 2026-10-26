'use strict';

// 1769. Minimum Number of Operations to Move All Balls to Each Box: accumulate movement costs in one sweep from each side.
// O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only.
function solve(boxes) {
  const result = new Array(boxes.length).fill(0);
  let balls = 0;
  let cost = 0;
  for (let index = 0; index < boxes.length; index += 1) {
    result[index] += cost;
    if (boxes[index] === '1') balls += 1;
    cost += balls;
  }
  balls = 0;
  cost = 0;
  for (let index = boxes.length - 1; index >= 0; index -= 1) {
    result[index] += cost;
    if (boxes[index] === '1') balls += 1;
    cost += balls;
  }
  return result;
}

const minOperations = solve;
class Solution {
  minOperations(boxes) { return solve(boxes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
