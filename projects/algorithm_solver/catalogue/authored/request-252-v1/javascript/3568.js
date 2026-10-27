'use strict';

function solve(classroom, energy) {
    const rows = classroom.length;
    const cols = classroom[0].length;
    const size = rows * cols;
    const cells = classroom.join('');
    const litter = new Int32Array(size);
    let count = 0;
    let start = 0;
    for (let cell = 0; cell < size; cell++) {
        if (cells[cell] === 'S') start = cell;
        if (cells[cell] === 'L') litter[cell] = 1 << count++;
    }
    const target = (1 << count) - 1;
    if (!target) return 0;
    const neighbors = Array.from({ length: size }, () => []);
    for (let cell = 0; cell < size; cell++) {
        const r = Math.floor(cell / cols);
        const c = cell % cols;
        for (const [nr, nc] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) {
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && cells[nr * cols + nc] !== 'X') {
                neighbors[cell].push(nr * cols + nc);
            }
        }
    }
    const stride = energy + 1;
    const best = new Uint8Array(size * (target + 1));
    best[start] = energy + 1;
    let frontier = [start * stride + energy];
    let moves = 0;
    while (frontier.length) {
        const next = [];
        for (const state of frontier) {
            const remaining = state % stride;
            const positionMask = Math.floor(state / stride);
            const cell = positionMask % size;
            const mask = Math.floor(positionMask / size);
            if (mask === target) return moves;
            if (!remaining) continue;
            for (const other of neighbors[cell]) {
                const newMask = mask | litter[other];
                const newEnergy = cells[other] === 'R' ? energy : remaining - 1;
                const key = newMask * size + other;
                if (best[key] < newEnergy + 1) {
                    best[key] = newEnergy + 1;
                    next.push(key * stride + newEnergy);
                }
            }
        }
        frontier = next;
        moves++;
    }
    return -1;
}
module.exports = { solve };
