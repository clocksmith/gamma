"use strict";
//1074. Number of Submatrices That Sum to Target.
//Canonical definition: https://leetcode.com/problems/number-of-submatrices-that-sum-to-target/description/
//Separate correct-identity variant; supplied1074 dice source is preserved.
function solve(matrix,target) {
  const rows=matrix.length, cols=matrix[0].length;
  let answer=0;
  for (let top=0;top<rows;top++) {
    const sums=new Array(cols).fill(0);
    for (let bottom=top;bottom<rows;bottom++) {
      for (let col=0;col<cols;col++) sums[col]+=matrix[bottom][col];
      const frequencies=new Map([[0,1]]);
      let prefix=0;
      for (const value of sums) {
        prefix+=value;
        answer+=frequencies.get(prefix-target)||0;
        frequencies.set(prefix,(frequencies.get(prefix)||0)+1);
      }
    }
  }
  return answer;
}
const numSubmatrixSumTarget=solve;
class Solution { numSubmatrixSumTarget(matrix,target) { return solve(matrix,target); } }
if (typeof module!=="undefined") module.exports={solve,Solution,numSubmatrixSumTarget};
