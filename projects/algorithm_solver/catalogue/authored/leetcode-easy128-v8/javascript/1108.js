'use strict';

// 1108. Defanging an IP Address (Easy).
// Specification: https://leetcode.com/problems/defanging-an-ip-address/description/
// O(n) time and space; replace every period in the valid input address.
function solve(address) {
  return address.split('.').join('[.]');
}

const defangIPaddr = solve;
class Solution {
  defangIPaddr(address) { return solve(address); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, defangIPaddr };
