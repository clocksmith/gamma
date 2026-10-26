'use strict';

// 1307. Verbal Arithmetic Puzzle: column-wise carry backtracking over at most ten letters; exponential search, no input mutation.

function solve(words, result) {
  if (words.some(word => word.length > result.length)) return false;
  if (new Set(words.join('') + result).size > 10) return false;
  const leading = new Set([...words, result].filter(word => word.length > 1).map(word => word[0]));
  const assigned = new Map();
  const used = Array(10).fill(false);
  function search(column, row, total) {
    if (column === result.length) return total === 0;
    if (row < words.length) {
      const word = words[row];
      if (column >= word.length) return search(column, row + 1, total);
      const letter = word[word.length - column - 1];
      if (assigned.has(letter)) return search(column, row + 1, total + assigned.get(letter));
      for (let digit = 0; digit < 10; digit += 1) {
        if (used[digit] || (digit === 0 && leading.has(letter))) continue;
        assigned.set(letter, digit);
        used[digit] = true;
        const valid = search(column, row + 1, total + digit);
        used[digit] = false;
        assigned.delete(letter);
        if (valid) return true;
      }
      return false;
    }
    const letter = result[result.length - column - 1];
    const digit = total % 10;
    const carry = Math.floor(total / 10);
    if (assigned.has(letter)) return assigned.get(letter) === digit && search(column + 1, 0, carry);
    if (used[digit] || (digit === 0 && leading.has(letter))) return false;
    assigned.set(letter, digit);
    used[digit] = true;
    const valid = search(column + 1, 0, carry);
    used[digit] = false;
    assigned.delete(letter);
    return valid;
  }
  return search(0, 0, 0);
}

const isSolvable = solve;
class Solution {
  isSolvable(words, result) { return solve(words, result); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSolvable };
