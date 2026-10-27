function solve(m, k, nums) {
    const modulus = 1000000007n;
    const choose = Array.from({length: m + 1}, () => []);
    for (let n = 0; n <= m; ++n) {
        choose[n][0] = choose[n][n] = 1n;
        for (let c = 1; c < n; ++c) choose[n][c] = choose[n - 1][c - 1] + choose[n - 1][c];
    }
    const width = m + 1;
    const encode = (used, carry, ones) => (used * width + carry) * width + ones;
    let states = new Map([[encode(0, 0, 0), 1n]]);
    for (const value of nums) {
        const powers = [1n];
        for (let c = 1; c <= m; ++c) powers.push(powers[c - 1] * BigInt(value) % modulus);
        const weights = choose.map(row => row.map((coefficient, c) => coefficient * powers[c] % modulus));
        const following = new Map();
        for (const [key, ways] of states) {
            const ones = key % width;
            const carry = Math.floor(key / width) % width;
            const used = Math.floor(key / (width * width));
            for (let count = 0; count <= m - used; ++count) {
                const total = carry + count;
                const nextOnes = ones + total % 2;
                if (nextOnes > k) continue;
                const nextKey = encode(used + count, Math.floor(total / 2), nextOnes);
                const contribution = ways * weights[m - used][count];
                following.set(nextKey, ((following.get(nextKey) || 0n) + contribution) % modulus);
            }
        }
        states = following;
    }
    let answer = 0n;
    for (const [key, ways] of states) {
        let ones = key % width;
        let carry = Math.floor(key / width) % width;
        const used = Math.floor(key / (width * width));
        while (carry) { ones += carry % 2; carry = Math.floor(carry / 2); }
        if (used === m && ones === k) answer = (answer + ways) % modulus;
    }
    return Number(answer);
}
module.exports = {solve};
