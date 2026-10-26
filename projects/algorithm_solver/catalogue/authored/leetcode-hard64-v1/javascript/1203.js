'use strict';

// 1203. Sort Items by Groups Respecting Dependencies: separate group and item topological orders.
// O(n + m + E) time and space, E = prerequisite count. Inputs are preserved.
function solve(n, m, group, beforeItems) {
  const groups = group.slice();
  let groupCount = m;
  for (let item = 0; item < n; item += 1) {
    if (groups[item] === -1) {
      groups[item] = groupCount;
      groupCount += 1;
    }
  }
  const itemEdges = Array.from({ length: n }, () => []);
  const itemDegree = new Int32Array(n);
  const groupEdges = Array.from({ length: groupCount }, () => new Set());
  const groupDegree = new Int32Array(groupCount);
  for (let item = 0; item < n; item += 1) {
    for (const previous of beforeItems[item]) {
      itemEdges[previous].push(item);
      itemDegree[item] += 1;
      const source = groups[previous];
      const destination = groups[item];
      if (source !== destination && !groupEdges[source].has(destination)) {
        groupEdges[source].add(destination);
        groupDegree[destination] += 1;
      }
    }
  }
  function topological(edges, degree) {
    const order = [];
    for (let node = 0; node < degree.length; node += 1) {
      if (degree[node] === 0) order.push(node);
    }
    for (let head = 0; head < order.length; head += 1) {
      for (const following of edges[order[head]]) {
        degree[following] -= 1;
        if (degree[following] === 0) order.push(following);
      }
    }
    return order.length === edges.length ? order : [];
  }
  const itemOrder = topological(itemEdges, itemDegree);
  const groupOrder = topological(groupEdges, groupDegree);
  if (itemOrder.length !== n || groupOrder.length !== groupCount) return [];
  const buckets = Array.from({ length: groupCount }, () => []);
  for (const item of itemOrder) buckets[groups[item]].push(item);
  const answer = [];
  for (const identifier of groupOrder) {
    for (const item of buckets[identifier]) answer.push(item);
  }
  return answer;
}

const sortItems = solve;
class Solution {
  sortItems(n, m, group, beforeItems) { return solve(n, m, group, beforeItems); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortItems };
