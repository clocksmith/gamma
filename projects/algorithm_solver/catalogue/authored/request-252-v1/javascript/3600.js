'use strict';

function solve(n, edges, k) {
    function feasible(threshold) {
        const parent = Int32Array.from({ length: n }, (_, i) => i);
        const sizes = new Int32Array(n).fill(1);
        let components = n;
        function find(u) {
            while (parent[u] !== u) {
                parent[u] = parent[parent[u]];
                u = parent[u];
            }
            return u;
        }
        function union(u, v) {
            u = find(u); v = find(v);
            if (u === v) return false;
            if (sizes[u] < sizes[v]) [u, v] = [v, u];
            parent[v] = u;
            sizes[u] += sizes[v];
            components--;
            return true;
        }
        for (const [u, v, strength, must] of edges) {
            if (must && (strength < threshold || !union(u, v))) return false;
        }
        for (const [u, v, strength, must] of edges) {
            if (!must && strength >= threshold) union(u, v);
        }
        let used = 0;
        for (const [u, v, strength, must] of edges) {
            if (!must && strength < threshold && threshold <= 2 * strength && union(u, v)) used++;
        }
        return components === 1 && used <= k;
    }
    if (!feasible(0)) return -1;
    let low = 0, high = 0;
    for (const edge of edges) high = Math.max(high, 2 * edge[2]);
    while (low < high) {
        const mid = Math.floor((low + high + 1) / 2);
        if (feasible(mid)) low = mid;
        else high = mid - 1;
    }
    return low;
}

module.exports = { solve };
