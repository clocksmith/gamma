// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(c, connections, queries) {
    const parent = Array.from({length: c+1}, (_, i) => i);
    const size = new Int32Array(c+1).fill(1);
    function find(x) {
        while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; }
        return x;
    }
    for (let [a, b] of connections) {
        a = find(a); b = find(b);
        if (a === b) continue;
        if (size[a] < size[b]) [a, b] = [b, a];
        parent[b] = a; size[a] += size[b];
    }
    const groups = Array.from({length: c+1}, () => []);
    const roots = parent.map((_, node) => find(node));
    for (let node = 1; node <= c; node++) groups[roots[node]].push(node);
    const online = new Uint8Array(c+1).fill(1), positions = new Int32Array(c+1), answer = [];
    for (const [kind, node] of queries) {
        if (kind === 2) online[node] = 0;
        else if (online[node]) answer.push(node);
        else {
            const root = roots[node], group = groups[root];
            while (positions[root] < group.length && !online[group[positions[root]]]) positions[root]++;
            answer.push(positions[root] < group.length ? group[positions[root]] : -1);
        }
    }
    return answer;
}
module.exports = {solve};
