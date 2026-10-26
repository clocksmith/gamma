'use strict';

// 1310. XOR Queries of a Subarray: cancel the prefix before each query interval.
// O(n + q) time and O(n) auxiliary space excluding the result; inputs are read-only.
function solve(arr, queries) {
  const prefix = new Int32Array(arr.length + 1);
  for (let index = 0; index < arr.length; index += 1) prefix[index + 1] = prefix[index] ^ arr[index];
  return queries.map(([left, right]) => prefix[right + 1] ^ prefix[left]);
}

const xorQueries = solve;
class Solution {
  xorQueries(arr, queries) { return solve(arr, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, xorQueries };
