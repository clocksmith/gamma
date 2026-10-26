'use strict';

// 3486. Longest Special Path II.
// The second-largest predecessor depth of repeated values bounds a path containing at most one repeated pair; iterative O(n) time and space. Inputs are preserved.

function solve(edges, nums) {
  const graph = Array.from({ length: nums.length }, () => []);
  for (const [first, second, weight] of edges) { graph[first].push([second, weight]); graph[second].push([first, weight]); }
  const last = new Map(), distances = [], stack = [[0, -1, 0, -1, -1, false, -1]];
  let answer = 0, count = 1;
  while (stack.length) {
    let [node, parent, distance, largest, second, exiting, previous] = stack.pop();
    const value = nums[node];
    if (exiting) {
      distances.pop();
      if (previous === -1) last.delete(value); else last.set(value, previous);
      continue;
    }
    const depth = distances.length;
    previous = last.has(value) ? last.get(value) : -1;
    if (previous > largest) { second = largest; largest = previous; }
    else if (previous > second) second = previous;
    const start = second + 1;
    distances.push(distance); last.set(value, depth);
    const length = distance - distances[start], nodes = depth - start + 1;
    if (length > answer || (length === answer && nodes < count)) { answer = length; count = nodes; }
    stack.push([node, parent, distance, largest, second, true, previous]);
    for (const [child, weight] of graph[node]) if (child !== parent) stack.push([child, node, distance + weight, largest, second, false, -1]);
  }
  return [answer, count];
}

const longestSpecialPath = solve;
class Solution {
  longestSpecialPath(edges, nums) { return solve(edges, nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSpecialPath };
