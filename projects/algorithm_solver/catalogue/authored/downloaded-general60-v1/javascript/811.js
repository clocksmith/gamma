'use strict';

// 811. Subdomain Visit Count (Medium).
// Specification: https://leetcode.com/problems/subdomain-visit-count/description/
function solve(cpdomains) {
  const counts = {};
  for (const entry of cpdomains) {
    const space = entry.indexOf(' ');
    const count = Number(entry.slice(0, space));
    const domain = entry.slice(space + 1);
    const parts = domain.split('.');
    for (let i = 0; i < parts.length; i++) {
      const subdomain = parts.slice(i).join('.');
      counts[subdomain] = (counts[subdomain] || 0) + count;
    }
  }
  return Object.keys(counts).map((domain) => `${counts[domain]} ${domain}`).sort();
}
const subdomainVisits = solve;
class Solution { subdomainVisits(cpdomains) { return solve(cpdomains); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, subdomainVisits };
