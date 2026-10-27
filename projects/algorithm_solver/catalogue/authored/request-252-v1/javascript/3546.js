'use strict';

function solve(grid) {
    let total = 0;
    for (const row of grid) for (const value of row) total += value;
    let prefix = 0;
    for (let r = 0; r + 1 < grid.length; r++) {
        for (const value of grid[r]) prefix += value;
        if (2 * prefix === total) return true;
    }
    prefix = 0;
    for (let c = 0; c + 1 < grid[0].length; c++) {
        for (const row of grid) prefix += row[c];
        if (2 * prefix === total) return true;
    }
    return false;
}

module.exports = { solve };
