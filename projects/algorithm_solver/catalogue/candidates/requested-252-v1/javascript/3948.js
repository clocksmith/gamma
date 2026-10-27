'use strict';

// 3948. Lexicographically Maximum MEX Array.
// Specification: https://leetcode.com/problems/lexicographically-maximum-mex-array/description/
// O(n) time and O(n) space; take the shortest prefix realizing each suffix MEX. Inputs are preserved.
function solve(nums) {
  const size = nums.length;
  const suffixMex = new Int32Array(size);
  const present = new Uint8Array(size + 1);
  let mex = 0;
  for (let index = size - 1; index >= 0; index--) {
    if (nums[index] <= size) present[nums[index]] = 1;
    while (mex <= size && present[mex]) mex++;
    suffixMex[index] = mex;
  }
  const answer = [];
  const seen = new Int32Array(size + 1);
  let generation = 0;
  let start = 0;
  while (start < size) {
    const wanted = suffixMex[start];
    answer.push(wanted);
    if (wanted === 0) { start++; continue; }
    generation++;
    let needed = wanted;
    while (needed > 0) {
      const value = nums[start++];
      if (value < wanted && seen[value] !== generation) { seen[value] = generation; needed--; }
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
