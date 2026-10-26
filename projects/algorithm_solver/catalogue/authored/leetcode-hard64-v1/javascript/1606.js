'use strict';

// 1606. Find Servers That Handled Most Number of Requests: release-time heap and Fenwick order statistics for free servers.
// O((n + k) * log(k + 1)) time and O(k) space. Inputs are preserved.
function solve(k, arrival, load) {
  const tree = new Int32Array(k + 1);
  for (let index = 1; index <= k; index += 1) tree[index] = index & -index;
  function add(server, change) {
    for (let index = server + 1; index <= k; index += index & -index) tree[index] += change;
  }
  function prefix(length) {
    let total = 0;
    for (let index = length; index > 0; index -= index & -index) total += tree[index];
    return total;
  }
  let highestStep = 1;
  while (highestStep * 2 <= k) highestStep *= 2;
  function select(order) {
    let index = 0;
    for (let step = highestStep; step > 0; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following <= k && tree[following] < order) {
        order -= tree[following];
        index = following;
      }
    }
    return index;
  }
  const busy = [];
  const before = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  function push(value) {
    let index = busy.length;
    busy.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!before(value, busy[parent])) break;
      busy[index] = busy[parent];
      index = parent;
    }
    busy[index] = value;
  }
  function pop() {
    const first = busy[0];
    const last = busy.pop();
    if (busy.length > 0) {
      let index = 0;
      while (index * 2 + 1 < busy.length) {
        let child = index * 2 + 1;
        if (child + 1 < busy.length && before(busy[child + 1], busy[child])) child += 1;
        if (!before(busy[child], last)) break;
        busy[index] = busy[child];
        index = child;
      }
      busy[index] = last;
    }
    return first;
  }
  const handled = new Int32Array(k);
  for (let request = 0; request < arrival.length; request += 1) {
    const time = arrival[request];
    while (busy.length > 0 && busy[0][0] <= time) add(pop()[1], 1);
    const available = prefix(k);
    if (available === 0) continue;
    const earlier = prefix(request % k);
    const server = select(earlier < available ? earlier + 1 : 1);
    add(server, -1);
    handled[server] += 1;
    push([time + load[request], server]);
  }
  let best = 0;
  for (const count of handled) best = Math.max(best, count);
  const answer = [];
  for (let server = 0; server < k; server += 1) {
    if (handled[server] === best) answer.push(server);
  }
  return answer;
}

const busiestServers = solve;
class Solution {
  busiestServers(k, arrival, load) { return solve(k, arrival, load); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, busiestServers };
