'use strict';

function solve(coords) {
    const vertical = new Map();
    const horizontal = new Map();
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    function extend(map, key, value) {
        if (!map.has(key)) map.set(key, [value, value]);
        else {
            const span = map.get(key);
            span[0] = Math.min(span[0], value);
            span[1] = Math.max(span[1], value);
        }
    }
    for (const [x, y] of coords) {
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
        extend(vertical, x, y);
        extend(horizontal, y, x);
    }
    let answer = 0;
    for (const [x, [low, high]] of vertical) {
        answer = Math.max(answer, (high - low) * Math.max(x - minX, maxX - x));
    }
    for (const [y, [low, high]] of horizontal) {
        answer = Math.max(answer, (high - low) * Math.max(y - minY, maxY - y));
    }
    return answer || -1;
}
module.exports = { solve };
