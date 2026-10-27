'use strict';

function solve(n, nums, maxDiff, queries) {
    const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => nums[a] - nums[b]);
    const rank = new Int32Array(n);
    const values = order.map(u => nums[u]);
    order.forEach((u, i) => { rank[u] = i; });
    const component = new Int32Array(n);
    const farthest = new Int32Array(n);
    let right = 0;
    for (let left = 0; left < n; left++) {
        if (left) component[left] = component[left - 1] + (values[left] - values[left - 1] > maxDiff ? 1 : 0);
        while (right + 1 < n && values[right + 1] - values[left] <= maxDiff) right++;
        farthest[left] = right;
    }
    const jump = [farthest];
    for (let span = 2; span <= n; span *= 2) {
        const previous = jump[jump.length - 1];
        jump.push(Int32Array.from(previous, next => previous[next]));
    }
    return queries.map(([u, v]) => {
        let a = Math.min(rank[u], rank[v]);
        const b = Math.max(rank[u], rank[v]);
        if (a === b) return 0;
        if (component[a] !== component[b]) return -1;
        let distance = 0;
        for (let level = jump.length - 1; level >= 0; level--) {
            if (jump[level][a] < b) {
                a = jump[level][a];
                distance += 2 ** level;
            }
        }
        return distance + 1;
    });
}

module.exports = { solve };
