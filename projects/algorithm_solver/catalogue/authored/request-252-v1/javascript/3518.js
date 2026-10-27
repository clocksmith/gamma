'use strict';

function solve(s, k) {
    const counts = new Int32Array(26);
    for (const ch of s) counts[ch.charCodeAt(0) - 97]++;
    let middle = '';
    const half = new Int32Array(26);
    for (let i = 0; i < 26; i++) {
        if (counts[i] % 2) middle = String.fromCharCode(97 + i);
        half[i] = Math.floor(counts[i] / 2);
    }
    function combinationsCapped(n, r, cap) {
        let value = 1;
        const limit = Math.min(r, n - r);
        for (let i = 1; i <= limit; i++) {
            value = value * (n - i + 1) / i;
            if (value >= cap) return cap;
        }
        return value;
    }
    function arrangements(cap) {
        let ways = 1;
        let used = 0;
        for (const count of half) {
            ways *= combinationsCapped(used + count, count, cap);
            if (ways >= cap) return cap;
            used += count;
        }
        return ways;
    }
    if (arrangements(k) < k) return '';
    const prefix = [];
    for (let pos = 0; pos < Math.floor(s.length / 2); pos++) {
        for (let letter = 0; letter < 26; letter++) {
            if (!half[letter]) continue;
            half[letter]--;
            const ways = arrangements(k);
            if (ways >= k) {
                prefix.push(String.fromCharCode(97 + letter));
                break;
            }
            k -= ways;
            half[letter]++;
        }
    }
    return prefix.join('') + middle + prefix.reverse().join('');
}
module.exports = { solve };
