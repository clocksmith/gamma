function solve(edges, queries) {
    const n = edges.length + 1;
    const adjacency = Array.from({length: n + 1}, () => []);
    for (const [u, v] of edges) { adjacency[u].push(v); adjacency[v].push(u); }
    const depth = new Int32Array(n + 1), parent = new Int32Array(n + 1);
    const order = [1];
    for (let index = 0; index < order.length; ++index) {
        const u = order[index];
        for (const v of adjacency[u]) {
            if (v !== parent[u]) { parent[v] = u; depth[v] = depth[u] + 1; order.push(v); }
        }
    }
    const ancestors = [parent];
    for (let level = 1; 2 ** level <= n; ++level) {
        const previous = ancestors[level - 1], current = new Int32Array(n + 1);
        for (let u = 1; u <= n; ++u) current[u] = previous[previous[u]];
        ancestors.push(current);
    }
    const powers = Array(n).fill(1);
    for (let i = 1; i < n; ++i) powers[i] = powers[i - 1] * 2 % 1000000007;
    function lca(u, v) {
        if (depth[u] < depth[v]) [u, v] = [v, u];
        const difference = depth[u] - depth[v];
        for (let level = 0; level < ancestors.length; ++level) {
            if ((difference >> level) & 1) u = ancestors[level][u];
        }
        if (u === v) return u;
        for (let level = ancestors.length - 1; level >= 0; --level) {
            if (ancestors[level][u] !== ancestors[level][v]) {
                u = ancestors[level][u]; v = ancestors[level][v];
            }
        }
        return parent[u];
    }
    return queries.map(([u, v]) => {
        const distance = depth[u] + depth[v] - 2 * depth[lca(u, v)];
        return distance ? powers[distance - 1] : 0;
    });
}
module.exports = {solve};
