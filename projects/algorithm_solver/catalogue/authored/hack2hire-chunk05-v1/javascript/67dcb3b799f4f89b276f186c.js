// Original hack2hire:67dcb3b799f4f89b276f186c; inferred public-preview contract; qualification unknown.
"use strict";
function referralLeaderboard(referrers,referrals) {
  const parent = new Map(), nodes = new Set([...referrers,...referrals]), pending = new Map([...nodes].map(n => [n,0])), totals = new Map([...nodes].map(n => [n,0]));
  referrers.forEach((source,i) => { parent.set(referrals[i],source); pending.set(source,pending.get(source)+1); });
  const queue = [...nodes].filter(n => pending.get(n) === 0);
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head]; if (!parent.has(node)) continue;
    const target = parent.get(node); totals.set(target,totals.get(target)+1+totals.get(node)); pending.set(target,pending.get(target)-1); if (!pending.get(target)) queue.push(target);
  }
  return [...new Set(referrers)].sort((a,b) => totals.get(b)-totals.get(a) || (a < b ? -1 : a > b ? 1 : 0)).slice(0,3).map(name => [name,totals.get(name)]);
}

const solve = referralLeaderboard;
module.exports = solve;
module.exports.referralLeaderboard = referralLeaderboard;
module.exports.Solution = class { referralLeaderboard(...args) { return referralLeaderboard(...args); } };
