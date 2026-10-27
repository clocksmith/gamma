'use strict';

function solve(edges, online, k) {
    const n = online.length;
    const graph = Array.from({ length: n }, () => []);
    const indegree = new Int32Array(n);
    for (const [u, v, cost] of edges) {
        graph[u].push([v, cost]);
        indegree[v]++;
    }
    const order = [];
    for (let u = 0; u < n; u++) if (!indegree[u]) order.push(u);
    for (let i = 0; i < order.length; i++) {
        for (const [v] of graph[order[i]]) if (--indegree[v] === 0) order.push(v);
    }
    function feasible(threshold) {
        const distance = new Float64Array(n).fill(Infinity);
        distance[0] = 0;
        for (const u of order) {
            if (!online[u] || distance[u] > k) continue;
            for (const [v, cost] of graph[u]) {
                if (online[v] && cost >= threshold) distance[v] = Math.min(distance[v], distance[u] + cost);
            }
        }
        return distance[n - 1] <= k;
    }
    if (!feasible(0)) return -1;
    let low = 0, high = 0;
    for (const edge of edges) high = Math.max(high, edge[2]);
    while (low < high) {
        const mid = Math.floor((low + high + 1) / 2);
        if (feasible(mid)) low = mid;
        else high = mid - 1;
    }
    return low;
}

module.exports = { solve };
