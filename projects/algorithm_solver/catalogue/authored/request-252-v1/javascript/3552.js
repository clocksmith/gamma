'use strict';

function solve(matrix) {
    const rows = matrix.length;
    const cols = matrix[0].length;
    const size = rows * cols;
    const portals = Array.from({ length: 26 }, () => []);
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const letter = matrix[r].charCodeAt(c) - 65;
            if (letter >= 0 && letter < 26) portals[letter].push(r * cols + c);
        }
    }
    // A growable typed circular deque avoids Array.shift and retained prefixes.
    let deque = new Int32Array(16);
    let head = 0;
    let length = 0;
    function push(value, front) {
        if (length === deque.length) {
            const grown = new Int32Array(deque.length * 2);
            for (let i = 0; i < length; i++) grown[i] = deque[(head + i) % deque.length];
            deque = grown;
            head = 0;
        }
        if (front) head = (head - 1 + deque.length) % deque.length;
        deque[(head + (front ? 0 : length)) % deque.length] = value;
        length++;
    }
    const distance = new Int32Array(size).fill(size + 1);
    const settled = new Uint8Array(size);
    const used = new Uint8Array(26);
    distance[0] = 0;
    push(0, false);
    while (length) {
        const cell = deque[head];
        head = (head + 1) % deque.length;
        length--;
        if (settled[cell]) continue;
        settled[cell] = 1;
        if (cell === size - 1) return distance[cell];
        const r = Math.floor(cell / cols);
        const c = cell % cols;
        const letter = matrix[r].charCodeAt(c) - 65;
        if (letter >= 0 && letter < 26 && !used[letter]) {
            used[letter] = 1;
            for (const other of portals[letter]) {
                if (distance[other] > distance[cell]) {
                    distance[other] = distance[cell];
                    push(other, true);
                }
            }
        }
        for (const [nr, nc] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) {
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols || matrix[nr][nc] === '#') continue;
            const other = nr * cols + nc;
            if (distance[other] > distance[cell] + 1) {
                distance[other] = distance[cell] + 1;
                push(other, false);
            }
        }
    }
    return -1;
}
module.exports = { solve };
