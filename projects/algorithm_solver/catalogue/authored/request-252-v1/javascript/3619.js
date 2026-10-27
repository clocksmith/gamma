'use strict';

function solve(grid, k) {
    const rows = grid.length;
    const cols = grid[0].length;
    const seen = new Uint8Array(rows * cols);
    let answer = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const start = r * cols + c;
            if (seen[start] || !grid[r][c]) continue;
            seen[start] = 1;
            const stack = [start];
            let total = 0;
            while (stack.length) {
                const cell = stack.pop();
                const x = Math.floor(cell / cols);
                const y = cell % cols;
                total += grid[x][y];
                for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) {
                    if (nx < 0 || nx >= rows || ny < 0 || ny >= cols) continue;
                    const other = nx * cols + ny;
                    if (!seen[other] && grid[nx][ny] > 0) {
                        seen[other] = 1;
                        stack.push(other);
                    }
                }
            }
            if (total % k === 0) answer++;
        }
    }
    return answer;
}
module.exports = { solve };
