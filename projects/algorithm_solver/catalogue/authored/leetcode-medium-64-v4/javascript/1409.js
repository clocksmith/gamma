'use strict';

// 1409. Queries on a Permutation With Key: reserve front positions and maintain occupied ranks in a Fenwick tree.
// O((m + q) log(m + q + 1)) time and O(m + q) auxiliary space; inputs are read-only.
function solve(queries, m) {
  const count = queries.length;
  const tree = new Int32Array(m + count + 1);
  const positions = new Int32Array(m + 1);
  function update(index, delta) {
    while (index < tree.length) {
      tree[index] += delta;
      index += index & -index;
    }
  }
  function prefix(index) {
    let total = 0;
    while (index > 0) {
      total += tree[index];
      index -= index & -index;
    }
    return total;
  }
  for (let value = 1; value <= m; value += 1) {
    positions[value] = count + value;
    update(positions[value], 1);
  }
  let front = count;
  const result = [];
  for (const value of queries) {
    result.push(prefix(positions[value] - 1));
    update(positions[value], -1);
    positions[value] = front;
    update(front, 1);
    front -= 1;
  }
  return result;
}

const processQueries = solve;
class Solution {
  processQueries(queries, m) { return solve(queries, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, processQueries };
