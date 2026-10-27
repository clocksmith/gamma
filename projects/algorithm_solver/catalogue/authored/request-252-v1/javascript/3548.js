// Original candidate; contract and evidence: ../batch1/manifest.json
"use strict";
function solve(grid) {
    function sweep(transposed) {
        const rows = transposed ? grid[0].length : grid.length;
        const columns = transposed ? grid.length : grid[0].length;
        const at = (r, c) => transposed ? grid[c][r] : grid[r][c];
        const left = new Map(), right = new Map();
        let total = 0, prefix = 0;
        for (const row of grid) for (const value of row) {
            right.set(value, (right.get(value) || 0) + 1);
            total += value;
        }
        for (let cut = 1; cut < rows; cut++) {
            for (let column = 0; column < columns; column++) {
                const value = at(cut-1, column);
                left.set(value, (left.get(value) || 0) + 1);
                right.set(value, right.get(value) - 1);
                prefix += value;
            }
            const difference = 2*prefix - total;
            if (difference === 0) return true;
            const [start, end, counts] = difference > 0 ? [0, cut, left] : [cut, rows, right];
            const target = Math.abs(difference);
            if ((end-start)*columns <= 1) continue;
            let possible;
            if (end-start === 1) possible = at(start, 0) === target || at(start, columns-1) === target;
            else if (columns === 1) possible = at(start, 0) === target || at(end-1, 0) === target;
            else possible = (counts.get(target) || 0) > 0;
            if (possible) return true;
        }
        return false;
    }
    return sweep(false) || sweep(true);
}
module.exports = {solve};
