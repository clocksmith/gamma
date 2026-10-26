'use strict';

// 1345. Jump Game IV: BFS with each equal-value bucket consumed once; O(n) expected time and O(n) space.

function solve(arr) {
  const positions = new Map();
  for (let index = 0; index < arr.length; index += 1) {
    if (!positions.has(arr[index])) positions.set(arr[index], []);
    positions.get(arr[index]).push(index);
  }
  const seen = Array(arr.length).fill(false);
  seen[0] = true;
  const queue = [[0, 0]];
  for (let head = 0; head < queue.length; head += 1) {
    const [index, distance] = queue[head];
    if (index === arr.length - 1) return distance;
    const neighbors = positions.get(arr[index]) || [];
    positions.delete(arr[index]);
    neighbors.push(index - 1, index + 1);
    for (const neighbor of neighbors) {
      if (neighbor >= 0 && neighbor < arr.length && !seen[neighbor]) {
        seen[neighbor] = true;
        queue.push([neighbor, distance + 1]);
      }
    }
  }
  return -1;
}

const minJumps = solve;
class Solution {
  minJumps(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minJumps };
