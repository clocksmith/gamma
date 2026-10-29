"use strict";
// Hack2Hire 69ab56434b133b6a8f3a68a2 (Crypto Block Mining, variant 3) over an INFERRED spec; qualification unknown.
function solve(transactions, blockSize) {
  const index = new Map(transactions.map((t, i) => [t[0], i]));
  const children = transactions.map(() => []), roots = [];
  transactions.forEach((t, i) => (t[3] === null ? roots : children[index.get(t[3])]).push(i));
  const order = [], subtreeEnd = new Array(transactions.length);
  const stack = roots.slice().reverse().map(node => [node, false]);
  while (stack.length) { // iterative preorder recording where each subtree ends
    const [node, done] = stack.pop();
    if (done) { subtreeEnd[node] = order.length; continue; }
    order.push(node);
    stack.push([node, true]);
    for (let c = children[node].length - 1; c >= 0; c--) stack.push([children[node][c], false]);
  }
  const n = order.length, best = [];
  for (let i = 0; i <= n; i++) best.push(new Float64Array(blockSize + 1));
  for (let position = n - 1; position >= 0; position--) {
    const node = order[position], size = transactions[node][1], fee = transactions[node][2];
    const skip = best[subtreeEnd[node]], take = best[position + 1], here = best[position];
    for (let capacity = 0; capacity <= blockSize; capacity++) {
      let value = skip[capacity];
      if (size <= capacity && take[capacity - size] + fee > value) value = take[capacity - size] + fee;
      here[capacity] = value;
    }
  }
  return best[0][blockSize];
}
function maxFeesWithDependencies(transactions, blockSize) { return solve(transactions, blockSize); }
module.exports = solve;
module.exports.maxFeesWithDependencies = maxFeesWithDependencies;
