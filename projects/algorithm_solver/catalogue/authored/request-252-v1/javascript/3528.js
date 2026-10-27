// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(conversions) {
    const graph = Array.from({length: conversions.length + 1}, () => []);
    for (const [source, target, factor] of conversions) graph[source].push([target, factor]);
    const answer = new Array(graph.length).fill(0);
    answer[0] = 1;
    const stack = [0];
    while (stack.length) {
        const source = stack.pop();
        for (const [target, factor] of graph[source]) {
            answer[target] = Number(BigInt(answer[source]) * BigInt(factor) % 1000000007n);
            stack.push(target);
        }
    }
    return answer;
}
module.exports = {solve};
