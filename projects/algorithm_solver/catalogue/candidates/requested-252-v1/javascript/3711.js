/**
 * 3711. Maximum Transactions Without Negative Balance
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(transactions).
 * Algorithm: Greedily include a transaction; if a prefix becomes negative, remove its most negative selected transaction.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Balance magnitude <= 10^14 and count <= 100000; exact Number/int.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/maximum-transactions-without-negative-balance/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3711.Maximum%20Transactions%20Without%20Negative%20Balance/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Only one removal is required after each new amount: the removed negative is no greater than that newly added negative.
 */

class MinHeap {
  constructor(less = (left, right) => left < right) {
    this.items = [];
    this.less = less;
  }
  get size() {
    return this.items.length;
  }
  push(value) {
    const items = this.items;
    let position = items.length;
    items.push(value);
    while (position > 0) {
      const parent = Math.floor((position - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[position] = items[parent];
      position = parent;
    }
    items[position] = value;
  }
  pop() {
    const items = this.items;
    if (items.length === 0) throw new RangeError("Empty heap.");
    const result = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let position = 0;
      while (2 * position + 1 < items.length) {
        let child = 2 * position + 1;
        if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
        if (!this.less(items[child], last)) break;
        items[position] = items[child];
        position = child;
      }
      items[position] = last;
    }
    return result;
  }
}

function solve(transactions) {
  const negativeChoices = new MinHeap();
  let balance = 0;
  let count = 0;
  for (const amount of transactions) {
    balance += amount;
    count += 1;
    if (amount < 0) negativeChoices.push(amount);
    if (balance < 0) {
      balance -= negativeChoices.pop();
      count -= 1;
    }
  }
  return count;
}

function maxTransactions(transactions) {
  return solve(transactions);
}

class Solution {
  maxTransactions(transactions) {
    return solve(transactions);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxTransactions, Solution };
}
