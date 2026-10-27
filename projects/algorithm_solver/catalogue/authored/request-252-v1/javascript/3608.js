function solve(n, edges, k) {
    const parent = Array.from({length: n}, (_, i) => i), size = Array(n).fill(1);
    function find(vertex) {
        while (vertex !== parent[vertex]) {
            parent[vertex] = parent[parent[vertex]];
            vertex = parent[vertex];
        }
        return vertex;
    }
    const ordered = edges.slice().sort((a, b) => b[2] - a[2]);
    let components = n, index = 0;
    while (index < ordered.length) {
        const time = ordered[index][2];
        while (index < ordered.length && ordered[index][2] === time) {
            let a = find(ordered[index][0]), b = find(ordered[index][1]);
            if (a !== b) {
                if (size[a] < size[b]) [a, b] = [b, a];
                parent[b] = a;
                size[a] += size[b];
                --components;
            }
            ++index;
        }
        if (components < k) return time;
    }
    return 0;
}
module.exports = {solve};
