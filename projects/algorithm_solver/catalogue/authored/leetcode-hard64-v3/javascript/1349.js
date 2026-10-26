'use strict';

// 1349. Maximum Students Taking Exam: compatible row masks; O(rows*4^columns) time and O(2^columns) space.

function solve(seats) {
  const columns = seats[0].length;
  let previous = new Map([[0, 0]]);
  for (const row of seats) {
    let available = 0;
    for (let column = 0; column < columns; column += 1) {
      if (row[column] === '.') available |= 1 << column;
    }
    const current = new Map();
    for (let mask = available; ; mask = (mask - 1) & available) {
      if ((mask & (mask << 1)) === 0) {
        let count = 0;
        for (let bits = mask; bits !== 0; bits &= bits - 1) count += 1;
        for (const [before, value] of previous) {
          if ((mask & (before << 1)) === 0 && (mask & (before >> 1)) === 0) {
            current.set(mask, Math.max(current.get(mask) || 0, value + count));
          }
        }
      }
      if (mask === 0) break;
    }
    previous = current;
  }
  let answer = 0;
  for (const value of previous.values()) answer = Math.max(answer, value);
  return answer;
}

const maxStudents = solve;
class Solution {
  maxStudents(seats) { return solve(seats); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxStudents };
