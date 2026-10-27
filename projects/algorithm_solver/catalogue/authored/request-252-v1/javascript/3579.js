function solve(word1, word2) {
    const n = word1.length;
    const first = [...word1].map(character => character.charCodeAt(0) - 97);
    const second = [...word2].map(character => character.charCodeAt(0) - 97);
    function cost(left, right, reverse) {
        const unmatched = new Int32Array(26 * 26);
        let operations = Number(reverse);
        for (let offset = 0; offset <= right - left; ++offset) {
            const a = first[reverse ? right - offset : left + offset];
            const b = second[left + offset];
            if (a === b) continue;
            const opposite = b * 26 + a;
            if (unmatched[opposite]) --unmatched[opposite];
            else { ++unmatched[a * 26 + b]; ++operations; }
        }
        return operations;
    }
    const best = Array(n + 1).fill(n + 1);
    best[0] = 0;
    for (let end = 1; end <= n; ++end) {
        for (let start = 0; start < end; ++start) {
            const edits = Math.min(cost(start, end - 1, false), cost(start, end - 1, true));
            best[end] = Math.min(best[end], best[start] + edits);
        }
    }
    return best[n];
}
module.exports = {solve};
