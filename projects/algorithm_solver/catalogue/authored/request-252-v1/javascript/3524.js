function solve(nums, k) {
    const result = Array(k).fill(0);
    let endings = Array(k).fill(0);
    for (const value of nums) {
        const remainder = value % k;
        const current = Array(k).fill(0);
        current[remainder] = 1;
        for (let previous = 0; previous < k; ++previous) {
            current[(previous * remainder) % k] += endings[previous];
        }
        for (let r = 0; r < k; ++r) result[r] += current[r];
        endings = current;
    }
    return result;
}
module.exports = {solve};
