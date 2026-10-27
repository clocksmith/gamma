'use strict';

function solve(par, vals, queries) {
    const n = par.length;
    const children = Array.from({ length: n }, () => []);
    for (let u = 1; u < n; u++) children[par[u]].push(u);
    const narvetholi = [par, vals, queries];
    const pathXor = new Int32Array(n);
    pathXor[0] = vals[0];
    const euler = [];
    const tin = new Int32Array(n);
    const stack = [0];
    while (stack.length) {
        const u = stack.pop();
        tin[u] = euler.length;
        euler.push(u);
        for (let i = children[u].length - 1; i >= 0; i--) {
            const v = children[u][i];
            pathXor[v] = pathXor[u] ^ vals[v];
            stack.push(v);
        }
    }
    const size = new Int32Array(n).fill(1);
    const heavy = new Int32Array(n).fill(-1);
    for (let i = n - 1; i >= 0; i--) {
        const u = euler[i];
        for (const v of children[u]) {
            size[u] += size[v];
            if (heavy[u] === -1 || size[v] > size[heavy[u]]) heavy[u] = v;
        }
    }
    const values = [...new Set(pathXor)].sort((a, b) => a - b);
    const rank = new Map(values.map((value, i) => [value, i]));
    const ranks = Int32Array.from(pathXor, value => rank.get(value));
    const frequency = new Int32Array(values.length);
    const bit = new Int32Array(values.length + 1);
    let distinct = 0;
    function update(u, delta) {
        const r = ranks[u];
        const old = frequency[r];
        frequency[r] += delta;
        const change = Number(frequency[r] > 0) - Number(old > 0);
        if (change) {
            distinct += change;
            for (let i = r + 1; i < bit.length; i += i & -i) bit[i] += change;
        }
    }
    function kth(k) {
        let index = 0;
        let step = 1;
        while (step * 2 <= values.length) step *= 2;
        for (; step; step = Math.floor(step / 2)) {
            const next = index + step;
            if (next < bit.length && bit[next] < k) {
                index = next;
                k -= bit[next];
            }
        }
        return values[index];
    }
    const grouped = Array.from({ length: n }, () => []);
    queries.forEach(([u, k], i) => grouped[u].push([i, k]));
    const answer = new Array(queries.length).fill(-1);
    // Events avoid recursion limits on a 50,000-node chain.
    const events = [[0, true, false]];
    while (events.length) {
        const [u, keep, collect] = events.pop();
        if (!collect) {
            events.push([u, keep, true]);
            if (heavy[u] !== -1) events.push([heavy[u], true, false]);
            for (const v of children[u]) if (v !== heavy[u]) events.push([v, false, false]);
            continue;
        }
        for (const v of children[u]) {
            if (v !== heavy[u]) {
                for (let i = tin[v]; i < tin[v] + size[v]; i++) update(euler[i], 1);
            }
        }
        update(u, 1);
        for (const [index, k] of grouped[u]) if (k <= distinct) answer[index] = kth(k);
        if (!keep) {
            for (let i = tin[u]; i < tin[u] + size[u]; i++) update(euler[i], -1);
        }
    }
    return answer;
}

module.exports = { solve };
