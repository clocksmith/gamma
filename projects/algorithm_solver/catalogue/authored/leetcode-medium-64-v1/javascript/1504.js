'use strict';

// 1504. Count Submatrices With All Ones: sum histogram subarray minima with a counted monotonic stack.
// O(rows * columns) time and O(columns) auxiliary space; inputs are read-only.
function solve(mat) {
  const heights = new Array(mat[0].length).fill(0);
  let answer = 0;
  for (const row of mat) {
    const stack = [];
    let endingHere = 0;
    for (let column = 0; column < row.length; column += 1) {
      heights[column] = row[column] ? heights[column] + 1 : 0;
      const height = heights[column];
      let width = 1;
      while (stack.length && stack[stack.length - 1][0] >= height) {
        const [oldHeight, oldWidth] = stack.pop();
        endingHere -= oldHeight * oldWidth;
        width += oldWidth;
      }
      stack.push([height, width]);
      endingHere += height * width;
      answer += endingHere;
    }
  }
  return answer;
}

const numSubmat = solve;
class Solution {
  numSubmat(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numSubmat };
