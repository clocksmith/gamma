'use strict';

// 929. Unique Email Addresses (Easy).
// Specification: https://leetcode.com/problems/unique-email-addresses/description/
// O(total characters) expected time and space; normalize only the local part.
function solve(emails) {
  const addresses = new Set();
  for (const email of emails) {
    const separator = email.indexOf('@');
    const local = email.slice(0, separator).split('+')[0].split('.').join('');
    addresses.add(local + email.slice(separator));
  }
  return addresses.size;
}

const numUniqueEmails = solve;
class Solution {
  numUniqueEmails(emails) { return solve(emails); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numUniqueEmails };
