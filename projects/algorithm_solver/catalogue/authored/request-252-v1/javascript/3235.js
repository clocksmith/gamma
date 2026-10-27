// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(xCorner, yCorner, circles) {
    const width = BigInt(xCorner), height = BigInt(yCorner);
    const disks = circles.map(row => row.map(BigInt));
    const n = disks.length;
    const parent = Array.from({length: n + 2}, (_, i) => i);
    const size = new Int32Array(n + 2).fill(1);
    function find(x) {
        while (parent[x] !== x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }
    function union(a, b) {
        a = find(a); b = find(b);
        if (a === b) return;
        if (size[a] < size[b]) [a, b] = [b, a];
        parent[b] = a;
        size[a] += size[b];
    }
    const square = x => x * x;
    for (let i = 0; i < n; i++) {
        const [x, y, r] = disks[i];
        const rr = r * r;
        if (square(x) + square(y) <= rr || square(x-width) + square(y-height) <= rr) {
            return false;
        }
        const dx = x > width ? x - width : 0n;
        const dy = y > height ? y - height : 0n;
        if (square(x) + square(dy) <= rr || square(y-height) + square(dx) <= rr) union(i, n);
        if (square(y) + square(dx) <= rr || square(x-width) + square(dy) <= rr) union(i, n+1);
        for (let j = 0; j < i; j++) {
            const [a, b, radius] = disks[j];
            const total = r + radius;
            if (square(x-a) + square(y-b) > square(total)) continue;
            // An intersection outside the top/right boundary cannot create a
            // new barrier unless its disks already join through that boundary.
            if (x*radius + a*r <= width*total && y*radius + b*r <= height*total) union(i, j);
        }
        if (find(n) === find(n+1)) return false;
    }
    return true;
}
module.exports = {solve};
