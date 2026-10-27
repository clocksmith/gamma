'use strict';

function solve(x, y) {
    const best = new Map();
    for (let i = 0; i < x.length; i++) best.set(x[i], Math.max(best.get(x[i]) || 0, y[i]));
    if (best.size < 3) return -1;
    let first = 0, second = 0, third = 0;
    for (const value of best.values()) {
        if (value >= first) [first, second, third] = [value, first, second];
        else if (value >= second) [second, third] = [value, second];
        else if (value > third) third = value;
    }
    return first + second + third;
}

module.exports = { solve };
