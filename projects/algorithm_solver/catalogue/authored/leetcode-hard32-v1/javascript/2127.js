'use strict';

// 2127. Maximum Employees to Be Invited to a Meeting.
// O(n) time and space; iterative graph processing avoids deep recursion.
function solve(favorite) {
  const size = favorite.length;
  const indegree = new Int32Array(size);
  const depth = new Int32Array(size).fill(1);
  for (const node of favorite) indegree[node] += 1;
  const queue = [];
  for (let index = 0; index < size; index += 1) if (indegree[index] === 0) queue.push(index);
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    const neighbor = favorite[node];
    depth[neighbor] = Math.max(depth[neighbor], depth[node] + 1);
    indegree[neighbor] -= 1;
    if (indegree[neighbor] === 0) queue.push(neighbor);
  }
  let longest = 0;
  let pairs = 0;
  for (let start = 0; start < size; start += 1) {
    if (indegree[start] === 0) continue;
    let length = 0;
    let node = start;
    while (indegree[node] !== 0) {
      indegree[node] = 0;
      length += 1;
      node = favorite[node];
    }
    if (length === 2) pairs += depth[start] + depth[favorite[start]];
    else longest = Math.max(longest, length);
  }
  return Math.max(longest, pairs);
}

const maximumInvitations = solve;
class Solution {
  maximumInvitations(favorite) { return solve(favorite); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumInvitations };
