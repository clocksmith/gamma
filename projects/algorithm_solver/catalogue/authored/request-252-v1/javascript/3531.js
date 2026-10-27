function solve(n, buildings) {
    const rows = new Map(), columns = new Map();
    function include(map, key, value) {
        const range = map.get(key) || [value, value];
        range[0] = Math.min(range[0], value);
        range[1] = Math.max(range[1], value);
        map.set(key, range);
    }
    for (const [x, y] of buildings) {
        include(rows, x, y);
        include(columns, y, x);
    }
    let result = 0;
    for (const [x, y] of buildings) {
        const row = rows.get(x), column = columns.get(y);
        if (row[0] < y && y < row[1] && column[0] < x && x < column[1]) ++result;
    }
    return result;
}
module.exports = {solve};
