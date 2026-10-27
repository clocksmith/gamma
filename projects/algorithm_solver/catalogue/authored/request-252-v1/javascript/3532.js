'use strict';

function solve(n, nums, maxDiff, queries) {
    const component = new Int32Array(n);
    for (let i = 1; i < n; i++) {
        component[i] = component[i - 1] + (nums[i] - nums[i - 1] > maxDiff ? 1 : 0);
    }
    return queries.map(([u, v]) => component[u] === component[v]);
}
module.exports = { solve };
