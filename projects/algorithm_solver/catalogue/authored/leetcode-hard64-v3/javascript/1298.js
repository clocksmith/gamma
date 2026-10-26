'use strict';

// 1298. Maximum Candies You Can Get from Boxes: reachability with independent possession and key state; O(boxes+references) time and space.

function solve(status, candies, keys, containedBoxes, initialBoxes) {
  const available = Array(status.length).fill(false);
  const unlocked = status.map(Boolean);
  const opened = Array(status.length).fill(false);
  const queue = [];
  for (const box of initialBoxes) {
    available[box] = true;
    if (unlocked[box]) queue.push(box);
  }
  let total = 0;
  for (let head = 0; head < queue.length; head += 1) {
    const box = queue[head];
    if (opened[box]) continue;
    opened[box] = true;
    total += candies[box];
    for (const key of keys[box]) {
      if (!unlocked[key]) {
        unlocked[key] = true;
        if (available[key] && !opened[key]) queue.push(key);
      }
    }
    for (const child of containedBoxes[box]) {
      if (!available[child]) {
        available[child] = true;
        if (unlocked[child] && !opened[child]) queue.push(child);
      }
    }
  }
  return total;
}

const maxCandies = solve;
class Solution {
  maxCandies(status, candies, keys, containedBoxes, initialBoxes) { return solve(status, candies, keys, containedBoxes, initialBoxes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCandies };
