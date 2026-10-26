'use strict';

// 1916. Count Ways to Build Rooms in an Ant Colony. Tree hook-length formula with iterative subtree sizes; O(n+log MOD) modular operations, O(n) space. Inputs are preserved.

function solve(prevRoom) {
  const modulus = 1000000007n;
  const size = prevRoom.length;
  const children = Array.from({ length: size }, () => []);
  for (let node = 1; node < size; node += 1) children[prevRoom[node]].push(node);
  const order = [0];
  for (let head = 0; head < order.length; head += 1) {
    for (const child of children[order[head]]) order.push(child);
  }
  const subtree = Array(size).fill(1);
  for (let index = order.length - 1; index > 0; index -= 1) {
    const node = order[index];
    subtree[prevRoom[node]] += subtree[node];
  }
  let factorial = 1n;
  let denominator = 1n;
  for (let index = 0; index < size; index += 1) {
    factorial = factorial * BigInt(index + 1) % modulus;
    denominator = denominator * BigInt(subtree[index]) % modulus;
  }
  let exponent = modulus - 2n;
  let inverse = 1n;
  while (exponent > 0n) {
    if ((exponent & 1n) !== 0n) inverse = inverse * denominator % modulus;
    denominator = denominator * denominator % modulus;
    exponent >>= 1n;
  }
  return Number(factorial * inverse % modulus);
}

const waysToBuildRooms = solve;
class Solution {
  waysToBuildRooms(prevRoom) { return solve(prevRoom); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToBuildRooms };
