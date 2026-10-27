'use strict';

class NeighborSum {
    constructor(grid) {
        this.grid = grid.map(row => row.slice());
        this.position = new Map();
        for (let r = 0; r < grid.length; r++) {
            for (let c = 0; c < grid.length; c++) this.position.set(grid[r][c], [r, c]);
        }
    }
    sum(value, offsets) {
        const [r, c] = this.position.get(value);
        const n = this.grid.length;
        let total = 0;
        for (const [dr, dc] of offsets) {
            if (r + dr >= 0 && r + dr < n && c + dc >= 0 && c + dc < n) {
                total += this.grid[r + dr][c + dc];
            }
        }
        return total;
    }
    adjacentSum(value) {
        return this.sum(value, [[-1, 0], [1, 0], [0, -1], [0, 1]]);
    }
    diagonalSum(value) {
        return this.sum(value, [[-1, -1], [-1, 1], [1, -1], [1, 1]]);
    }
}
function solve(operations, args) {
    let service;
    return operations.map((operation, i) => {
        if (operation === 'NeighborSum') {
            service = new NeighborSum(...args[i]);
            return null;
        }
        if (operation === 'adjacentSum') return service.adjacentSum(...args[i]);
        if (operation === 'diagonalSum') return service.diagonalSum(...args[i]);
        throw new Error('Unsupported NeighborSum operation');
    });
}

module.exports = { solve, NeighborSum };
