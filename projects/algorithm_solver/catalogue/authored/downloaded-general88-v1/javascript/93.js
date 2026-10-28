'use strict';

// 93. Restore IP Addresses (Medium).
// Specification: https://leetcode.com/problems/restore-ip-addresses/description/
function solve(s) {
  const result = [];
  function backtrack(start, parts) {
    if (parts.length === 4) { if (start === s.length) result.push(parts.join('.')); return; }
    for (let length = 1; length <= 3 && start + length <= s.length; length++) {
      const segment = s.slice(start, start + length);
      if (segment.length > 1 && segment[0] === '0') break;
      if (Number(segment) > 255) break;
      parts.push(segment); backtrack(start + length, parts); parts.pop();
    }
  }
  backtrack(0, []);
  return result;
}
const restoreIpAddresses = solve;
class Solution { restoreIpAddresses(s) { return solve(s); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, restoreIpAddresses };
