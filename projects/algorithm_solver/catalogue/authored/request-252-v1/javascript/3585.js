// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(n, edges, queries) {
    const graph = Array.from({length: n}, () => []);
    for (const [a, b, weight] of edges) { graph[a].push([b, weight]); graph[b].push([a, weight]); }
    const parent = new Int32Array(n), depth = new Int32Array(n), distance = new Float64Array(n);
    const stack = [0];
    while (stack.length) {
        const node = stack.pop();
        for (const [child, weight] of graph[node]) if (child !== parent[node]) {
            parent[child] = node;
            depth[child] = depth[node]+1;
            distance[child] = distance[node]+weight;
            stack.push(child);
        }
    }
    const up = [parent];
    while (2 ** up.length <= n) {
        const previous = up[up.length-1];
        up.push(Int32Array.from(previous, ancestor => previous[ancestor]));
    }
    function lca(a, b) {
        if (depth[a] < depth[b]) [a, b] = [b, a];
        const difference = depth[a]-depth[b];
        for (let level = 0; level < up.length; level++) if ((difference >> level) & 1) a = up[level][a];
        if (a === b) return a;
        for (let level = up.length-1; level >= 0; level--) if (up[level][a] !== up[level][b]) {
            a = up[level][a]; b = up[level][b];
        }
        return parent[a];
    }
    return queries.map(([a, b]) => {
        const ancestor = lca(a, b);
        const total = distance[a]+distance[b]-2*distance[ancestor];
        if (total === 0) return a;
        if (2*(distance[a]-distance[ancestor]) >= total) {
            let node = a;
            for (let level = up.length-1; level >= 0; level--) {
                const candidate = up[level][node];
                if (depth[candidate] >= depth[ancestor] && 2*(distance[a]-distance[candidate]) < total) node = candidate;
            }
            return parent[node];
        }
        let node = b;
        for (let level = up.length-1; level >= 0; level--) {
            const candidate = up[level][node];
            if (depth[candidate] >= depth[ancestor] && 2*(distance[b]-distance[candidate]) <= total) node = candidate;
        }
        return node;
    });
}
module.exports = {solve};
