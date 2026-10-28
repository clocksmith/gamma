'use strict';

// 1089. Duplicate Zeros (Easy).
// Specification: https://leetcode.com/problems/duplicate-zeros/description/
function solve(arr) {
  const result = [];
  for (const value of arr) {
    if (result.length >= arr.length) break;
    result.push(value);
    if (value === 0 && result.length < arr.length) result.push(0);
  }
  return result;
}
function duplicateZeros(arr) {
  // Backward virtual positions preserve unread input; constant auxiliary space.
  let zeros=0;
  for (const value of arr) if (value===0) zeros++;
  const size=arr.length;
  for (let read=size-1;read>=0;read--) {
    const value=arr[read];
    const write=read+zeros;
    if (write<size) arr[write]=value;
    if (value===0) {
      zeros--;
      if (read+zeros<size) arr[read+zeros]=0;
    }
  }
}
class Solution { duplicateZeros(arr) { return duplicateZeros(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, duplicateZeros };
