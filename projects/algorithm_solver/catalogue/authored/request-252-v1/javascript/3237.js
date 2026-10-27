function solve(windows, queries) {
    const seen = new Set();
    const result = [];
    for (let i = queries.length - 1; i >= 0; --i) {
        const window = queries[i];
        if (!seen.has(window)) {
            seen.add(window);
            result.push(window);
        }
    }
    for (const window of windows) {
        if (!seen.has(window)) result.push(window);
    }
    return result;
}
module.exports = {solve};
