'use strict';

// 468. Validate IP Address. Check the explicit textual formats; do not accept compressed IPv6 or Unicode digits.

function solve(queryIP) {
  if (queryIP.includes('.')) {
    const parts = queryIP.split('.');
    if (parts.length === 4 && parts.every(part => /^[0-9]{1,3}$/.test(part) && (part.length === 1 || part[0] !== '0') && Number(part) <= 255)) return 'IPv4';
  } else {
    const parts = queryIP.split(':');
    if (parts.length === 8 && parts.every(part => /^[0-9a-fA-F]{1,4}$/.test(part))) return 'IPv6';
  }
  return 'Neither';
}

const validIPAddress = solve;
class Solution {
  validIPAddress(queryIP) { return solve(queryIP); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validIPAddress };
