'use strict';

// 721. Accounts Merge. Union shared-email accounts; return fresh sorted rows with unique emails.

class _DSU {
  constructor(n) { this.parent = Array.from({length: n}, (_, i) => i); this.size = Array(n).fill(1); }
  find(x) {
    while (this.parent[x] !== x) {
      this.parent[x] = this.parent[this.parent[x]];
      x = this.parent[x];
    }
    return x;
  }
  union(a, b) {
    a = this.find(a); b = this.find(b);
    if (a === b) return false;
    if (this.size[a] < this.size[b]) [a, b] = [b, a];
    this.parent[b] = a;
    this.size[a] += this.size[b];
    return true;
  }
}

function solve(accounts) {
  const dsu = new _DSU(accounts.length), owner = new Map();
  accounts.forEach((account, index) => {
    for (let i = 1; i < account.length; i += 1) {
      const email = account[i];
      if (owner.has(email)) dsu.union(index, owner.get(email)); else owner.set(email, index);
    }
  });
  const groups = new Map();
  for (const [email, index] of owner) {
    const root = dsu.find(index);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(email);
  }
  const answer = Array.from(groups, ([index, emails]) => [accounts[index][0], ...emails.sort()]);
  answer.sort((a, b) => {
    for (let i = 0; i < Math.min(a.length, b.length); i += 1) {
      if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
    }
    return a.length - b.length;
  });
  return answer;
}

const accountsMerge = solve;
class Solution {
  accountsMerge(accounts) { return solve(accounts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, accountsMerge };
