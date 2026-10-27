// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(edges) {
    const graph = Array.from({length: edges.length + 2}, () => []);
    for (const [a, b] of edges) { graph[a].push(b); graph[b].push(a); }
    const stack = [[1, 0, 0]];
    let deepest = 0;
    while (stack.length) {
        const [node, parent, depth] = stack.pop();
        deepest = Math.max(deepest, depth);
        for (const child of graph[node]) if (child !== parent) stack.push([child, node, depth+1]);
    }
    let answer = 1;
    for (let i = 1; i < deepest; i++) answer = answer * 2 % 1000000007;
    return answer;
}
module.exports = {solve};
