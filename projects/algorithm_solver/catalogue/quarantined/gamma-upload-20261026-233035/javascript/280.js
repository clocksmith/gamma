'use strict';
// 280. Wiggle Sort.
function solve(nums) {
  const values = nums.slice().sort((a, b) => a - b);
  let small = Math.floor((values.length - 1) / 2);
  let large = values.length - 1;
  for (let index = 0; index < nums.length; index += 1) nums[index] = index % 2 === 0 ? values[small--] : values[large--];
}
const wiggleSort = solve;
class Solution { wiggleSort(nums) { solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wiggleSort };
