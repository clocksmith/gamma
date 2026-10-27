function solve(words) {
    const n = words.length;
    function lcp(a, b) {
        let length = 0;
        while (length < Math.min(a.length, b.length) && a[length] === b[length]) ++length;
        return length;
    }
    const adjacent = [];
    for (let i = 0; i + 1 < n; ++i) adjacent.push(lcp(words[i], words[i + 1]));
    const prefix = Array(n).fill(0), suffix = Array(n).fill(0);
    for (let i = 0; i < adjacent.length; ++i) prefix[i + 1] = Math.max(prefix[i], adjacent[i]);
    for (let i = n - 2; i >= 0; --i) suffix[i] = Math.max(suffix[i + 1], adjacent[i]);
    return words.map((_, i) => {
        const unaffected = Math.max(prefix[Math.max(0, i - 1)], suffix[Math.min(n - 1, i + 1)]);
        const bridge = i > 0 && i + 1 < n ? lcp(words[i - 1], words[i + 1]) : 0;
        return Math.max(unaffected, bridge);
    });
}
module.exports = {solve};
