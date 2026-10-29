"use strict";
// Hack2Hire 67840e27d0faf7ec64cc3adb (Count Reversing Triples) over an INFERRED spec; qualification unknown.

function solve(nums) {
  const values = Array.from(new Set(nums)).sort((a, b) => a - b);
  const rank = new Map();
  values.forEach((v, i) => rank.set(v, i + 1));
  const size = values.length;
  const below = new Array(size + 2).fill(0); // below[r]: number of elements with rank < r
  for (const v of nums) below[rank.get(v) + 1]++;
  for (let r = 1; r < size + 2; r++) below[r] += below[r - 1];
  const tree = new Array(size + 1).fill(0);
  const equal = new Array(size + 1).fill(0);
  let total = 0;
  for (let j = 0; j < nums.length; j++) {
    const r = rank.get(nums[j]);
    let lessLeft = 0;
    for (let i = r - 1; i > 0; i -= i & -i) lessLeft += tree[i];
    const greaterLeft = j - lessLeft - equal[r];
    const lessRight = below[r] - lessLeft;
    total += greaterLeft * lessRight;
    equal[r]++;
    for (let i = r; i <= size; i += i & -i) tree[i]++;
  }
  return total;
}

function countTriplets(nums) { return solve(nums); }

module.exports = solve;
module.exports.countTriplets = countTriplets;
