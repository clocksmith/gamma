'use strict';

// 3266. Final Array State After K Multiplication Operations II.
// Simulate until every multiplication exceeds the initial maximum, then apply sorted cycles with modular powers; O((n+R) log n+n log k) time and O(n) space. Inputs are preserved.

class MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(items[parent], value) <= 0) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items;
    const answer = items[0];
    const last = items.pop();
    if (items.length === 0) return answer;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.compare(items[child + 1], items[child]) < 0) child += 1;
      if (this.compare(last, items[child]) <= 0) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = last;
    return answer;
  }
}

const MOD = 1000000007;
// Split multiplication keeps every intermediate integer below 2^53.
function multiplyMod(a, b) {
  return (a * (b % 32768) + ((a * Math.floor(b / 32768)) % MOD) * 32768) % MOD;
}
function powerMod(base, exponent) {
  let result = 1;
  while (exponent > 0) {
    if (exponent % 2 === 1) result = multiplyMod(result, base);
    base = multiplyMod(base, base);
    exponent = Math.floor(exponent / 2);
  }
  return result;
}

function solve(nums, k, multiplier) {
  if (multiplier === 1) return nums.map(value => value % MOD);
  let ceiling = 0;
  const heap = new MinHeap((a, b) => a[0] - b[0] || a[1] - b[1]);
  nums.forEach((value, index) => { ceiling = Math.max(ceiling, value); heap.push([value, index]); });
  while (k > 0 && heap.items[0][0] * multiplier <= ceiling) {
    const [value, index] = heap.pop();
    heap.push([value * multiplier, index]);
    k -= 1;
  }
  const rounds = Math.floor(k / nums.length), extra = k % nums.length;
  const factor = powerMod(multiplier, rounds), answer = Array(nums.length).fill(0);
  heap.items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  heap.items.forEach(([value, index], position) => {
    answer[index] = multiplyMod(value % MOD, factor);
    if (position < extra) answer[index] = multiplyMod(answer[index], multiplier);
  });
  return answer;
}

const getFinalState = solve;
class Solution {
  getFinalState(nums, k, multiplier) { return solve(nums, k, multiplier); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getFinalState };
