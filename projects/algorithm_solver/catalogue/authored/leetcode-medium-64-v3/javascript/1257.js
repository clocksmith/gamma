'use strict';

// 1257. Smallest Common Region: intersect parent chains in the region tree.
// O(r) time and O(r) auxiliary space for r region entries; inputs are read-only.
function solve(regions, region1, region2) {
  const parent = new Map();
  for (const group of regions) {
    for (let index = 1; index < group.length; index += 1) parent.set(group[index], group[0]);
  }
  const ancestors = new Set();
  let current = region1;
  while (current !== undefined) {
    ancestors.add(current);
    current = parent.get(current);
  }
  current = region2;
  while (!ancestors.has(current)) current = parent.get(current);
  return current;
}

const findSmallestRegion = solve;
class Solution {
  findSmallestRegion(regions, region1, region2) { return solve(regions, region1, region2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSmallestRegion };
