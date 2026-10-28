'use strict';

// 1801. Number of Orders in the Backlog (Medium).
// Specification: https://leetcode.com/problems/number-of-orders-in-the-backlog/description/
function heapPush(heap, value, compare) {
  heap.push(value);
  let index = heap.length - 1;
  while (index > 0) {
    const parent = Math.floor((index - 1) / 2);
    if (compare(heap[index], heap[parent]) < 0) { const tmp = heap[index]; heap[index] = heap[parent]; heap[parent] = tmp; index = parent; }
    else break;
  }
}
function heapPop(heap, compare) {
  const top = heap[0];
  const last = heap.pop();
  if (heap.length > 0) {
    heap[0] = last;
    let index = 0;
    while (true) {
      const left = 2 * index + 1; const right = 2 * index + 2; let smallest = index;
      if (left < heap.length && compare(heap[left], heap[smallest]) < 0) smallest = left;
      if (right < heap.length && compare(heap[right], heap[smallest]) < 0) smallest = right;
      if (smallest === index) break;
      const tmp = heap[index]; heap[index] = heap[smallest]; heap[smallest] = tmp; index = smallest;
    }
  }
  return top;
}
function solve(orders) {
  const buy = [];
  const sell = [];
  const buyCompare = (a, b) => b[0] - a[0];
  const sellCompare = (a, b) => a[0] - b[0];
  for (const [price, amount, orderType] of orders) {
    let remaining = amount;
    if (orderType === 0) {
      while (remaining > 0 && sell.length > 0 && sell[0][0] <= price) {
        const top = sell[0];
        const matched = Math.min(remaining, top[1]);
        remaining -= matched; top[1] -= matched;
        if (top[1] === 0) heapPop(sell, sellCompare);
      }
      if (remaining > 0) heapPush(buy, [price, remaining], buyCompare);
    } else {
      while (remaining > 0 && buy.length > 0 && buy[0][0] >= price) {
        const top = buy[0];
        const matched = Math.min(remaining, top[1]);
        remaining -= matched; top[1] -= matched;
        if (top[1] === 0) heapPop(buy, buyCompare);
      }
      if (remaining > 0) heapPush(sell, [price, remaining], sellCompare);
    }
  }
  let total = 0;
  for (const entry of buy) total += entry[1];
  for (const entry of sell) total += entry[1];
  return total % 1000000007;
}
const getNumberOfBacklogOrders = solve;
class Solution { getNumberOfBacklogOrders(orders) { return solve(orders); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getNumberOfBacklogOrders };
