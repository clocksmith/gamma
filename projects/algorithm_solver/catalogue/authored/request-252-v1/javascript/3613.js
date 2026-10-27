'use strict';

function solve(n, edges, k) {
    const parent = Int32Array.from({ length: n }, (_, i) => i);
    const size = new Int32Array(n).fill(1);
    let components = n;
    function find(u) {
        while (parent[u] !== u) {
            parent[u] = parent[parent[u]];
            u = parent[u];
        }
        return u;
    }
    if (components <= k) return 0;
    for (const [a, b, weight] of edges.slice().sort((x, y) => x[2] - y[2])) {
        let u = find(a), v = find(b);
        if (u === v) continue;
        if (size[u] < size[v]) [u, v] = [v, u];
        parent[v] = u;
        size[u] += size[v];
        components--;
        if (components <= k) return weight;
    }
    throw new Error('The input graph must be connected');
}

module.exports = { solve };
