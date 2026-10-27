'use strict';

function solve(nums) {
    const n = nums.length;
    if (n <= 2) return n;
    let bound = 1;
    while (bound <= n) bound *= 2;
    return bound;
}

module.exports = { solve };
