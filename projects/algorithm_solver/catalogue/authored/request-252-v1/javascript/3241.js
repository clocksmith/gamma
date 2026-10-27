'use strict';

function solve(edges) {
    const n = edges.length + 1;
    const graph = Array.from({ length: n }, () => []);
    for (const [u, v] of edges) {
        graph[u].push(v);
        graph[v].push(u);
    }
    const parent = new Int32Array(n).fill(-1);
    const order = [0];
    for (let i = 0; i < order.length; i++) {
        const u = order[i];
        for (const v of graph[u]) {
            if (v === parent[u]) continue;
            parent[v] = u;
            order.push(v);
        }
    }
    const first = new Int32Array(n);
    const second = new Int32Array(n);
    const owner = new Int32Array(n).fill(-1);
    for (let i = n - 1; i >= 0; i--) {
        const u = order[i];
        for (const v of graph[u]) {
            if (parent[v] !== u) continue;
            const distance = first[v] + 2 - v % 2;
            if (distance > first[u]) {
                second[u] = first[u];
                first[u] = distance;
                owner[u] = v;
            } else if (distance > second[u]) {
                second[u] = distance;
            }
        }
    }
    const upward = new Int32Array(n);
    const answer = new Array(n);
    for (const u of order) {
        answer[u] = Math.max(first[u], upward[u]);
        for (const v of graph[u]) {
            if (parent[v] !== u) continue;
            const sibling = owner[u] === v ? second[u] : first[u];
            upward[v] = Math.max(upward[u], sibling) + 2 - u % 2;
        }
    }
    return answer;
}
module.exports = { solve };
