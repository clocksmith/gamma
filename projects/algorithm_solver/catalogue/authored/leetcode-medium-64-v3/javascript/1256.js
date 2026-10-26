'use strict';

// 1256. Encode Number: remove the leading one from the binary representation of the successor.
// O(log(num + 2)) time and output space; inputs are read-only.
function solve(num) {
  return (num + 1).toString(2).slice(1);
}

const encode = solve;
class Solution {
  encode(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, encode };
