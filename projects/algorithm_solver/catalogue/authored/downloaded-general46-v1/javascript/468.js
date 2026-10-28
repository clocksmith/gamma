'use strict';

// 468. Validate IP Address (Medium).
// Specification: https://leetcode.com/problems/validate-ip-address/description/
function isIPv4(ip) {
  const parts = ip.split('.');
  if (parts.length !== 4) return false;
  for (const part of parts) {
    if (part.length === 0 || part.length > 3) return false;
    if (part.length > 1 && part[0] === '0') return false;
    for (const ch of part) { if (ch < '0' || ch > '9') return false; }
    if (Number(part) > 255) return false;
  }
  return true;
}
function isIPv6(ip) {
  const parts = ip.split(':');
  if (parts.length !== 8) return false;
  for (const part of parts) {
    if (part.length === 0 || part.length > 4) return false;
    for (const ch of part) {
      const lower = ch.toLowerCase();
      if (!((lower >= '0' && lower <= '9') || (lower >= 'a' && lower <= 'f'))) return false;
    }
  }
  return true;
}
function solve(ip) {
  if (isIPv4(ip)) return 'IPv4';
  if (isIPv6(ip)) return 'IPv6';
  return 'Neither';
}
const validIPAddress = solve;
class Solution { validIPAddress(ip) { return solve(ip); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, validIPAddress };
