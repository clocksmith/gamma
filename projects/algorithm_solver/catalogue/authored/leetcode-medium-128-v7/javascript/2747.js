'use strict';

// 2747. Count Zero Request Servers: answer sorted queries with an inclusive sliding time window of active servers.
// O(l log l + q log q + n) time and O(l + q + n) auxiliary space; inputs are read-only.
function solve(n, logs, x, queries) {
  const orderedLogs = logs.slice().sort((left, right) => left[1] - right[1]);
  const order = Array.from({ length: queries.length }, (_, index) => index)
    .sort((left, right) => queries[left] - queries[right]);
  const counts = new Int32Array(n + 1);
  const result = new Array(queries.length);
  let left = 0;
  let right = 0;
  let active = 0;
  for (const index of order) {
    const time = queries[index];
    while (right < orderedLogs.length && orderedLogs[right][1] <= time) {
      const server = orderedLogs[right][0];
      if (counts[server] === 0) active += 1;
      counts[server] += 1;
      right += 1;
    }
    while (left < right && orderedLogs[left][1] < time - x) {
      const server = orderedLogs[left][0];
      counts[server] -= 1;
      if (counts[server] === 0) active -= 1;
      left += 1;
    }
    result[index] = n - active;
  }
  return result;
}

const countServers = solve;
class Solution {
  countServers(n, logs, x, queries) { return solve(n, logs, x, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countServers };
