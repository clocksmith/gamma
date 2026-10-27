'use strict';

function solve(nums, k) {
    const n = nums.length;
    const prefix = new Int32Array(n + 1);
    for (let i = 0; i < n; i++) prefix[i + 1] = prefix[i] ^ nums[i];
    let previous = new Float64Array(n + 1).fill(Infinity);
    previous[0] = 0;
    for (let parts = 1; parts <= k; parts++) {
        const current = new Float64Array(n + 1).fill(Infinity);
        for (let end = parts; end <= n; end++) {
            for (let start = parts - 1; start < end; start++) {
                current[end] = Math.min(current[end], Math.max(previous[start], prefix[end] ^ prefix[start]));
            }
        }
        previous = current;
    }
    return previous[n];
}
module.exports = { solve };
