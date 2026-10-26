'use strict';

// 3161. Block Placement Queries: obstacle ranks with a Fenwick tree and prefix maximum gaps.
// O(q log M + M) time and O(M + q) space, M=max queried coordinate + 1. Inputs are preserved.
function solve(queries) {
  let limit = 0;
  for (const query of queries) limit = Math.max(limit, query[1]);
  limit += 1;
  const bit = new Int32Array(limit + 2);
  let size = 1;
  while (size < limit + 1) size *= 2;
  const gaps = new Int32Array(2 * size);
  function add(position) {
    for (let index = position + 1; index < bit.length; index += index & -index) bit[index] += 1;
  }
  function prefixCount(end) {
    let total = 0;
    while (end > 0) {
      total += bit[end];
      end -= end & -end;
    }
    return total;
  }
  function kth(rank) {
    let index = 0;
    let step = 1;
    while (step * 2 < bit.length) step *= 2;
    for (; step >= 1; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following < bit.length && bit[following] < rank) {
        rank -= bit[following];
        index = following;
      }
    }
    return index;
  }
  function update(position, length) {
    let index = position + size;
    gaps[index] = length;
    for (index = Math.floor(index / 2); index > 0; index = Math.floor(index / 2)) {
      gaps[index] = Math.max(gaps[2 * index], gaps[2 * index + 1]);
    }
  }
  function prefixMax(end) {
    let left = size;
    let right = size + end;
    let result = 0;
    while (left < right) {
      if (left & 1) result = Math.max(result, gaps[left++]);
      if (right & 1) result = Math.max(result, gaps[--right]);
      left = Math.floor(left / 2);
      right = Math.floor(right / 2);
    }
    return result;
  }
  add(0);
  add(limit);
  update(limit, limit);
  const answer = [];
  for (const query of queries) {
    const position = query[1];
    const rank = prefixCount(position + 1);
    const previous = kth(rank);
    if (query[0] === 1) {
      const following = kth(rank + 1);
      update(position, position - previous);
      update(following, following - position);
      add(position);
    } else {
      answer.push(Math.max(prefixMax(position + 1), position - previous) >= query[2]);
    }
  }
  return answer;
}

const getResults = solve;
class Solution {
  getResults(queries) { return solve(queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getResults };
