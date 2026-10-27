function solve(grid, k) {
    const answer = [];
    for (let top = 0; top + k <= grid.length; ++top) {
        const row = [];
        for (let left = 0; left + k <= grid[0].length; ++left) {
            const unique = new Set();
            for (let r = top; r < top + k; ++r) {
                for (let c = left; c < left + k; ++c) unique.add(grid[r][c]);
            }
            const values = [...unique].sort((a, b) => a - b);
            let minimum = Infinity;
            for (let i = 1; i < values.length; ++i) minimum = Math.min(minimum, values[i] - values[i - 1]);
            row.push(values.length < 2 ? 0 : minimum);
        }
        answer.push(row);
    }
    return answer;
}
module.exports = {solve};
