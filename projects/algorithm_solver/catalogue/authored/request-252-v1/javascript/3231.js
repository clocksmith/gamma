function solve(nums) {
    // Upper-bound patience sorting on negated values counts non-increasing chains.
    const tails = [];
    for (const value of nums) {
        const x = -value;
        let low = 0, high = tails.length;
        while (low < high) {
            const mid = Math.floor((low + high) / 2);
            if (tails[mid] <= x) low = mid + 1;
            else high = mid;
        }
        tails[low] = x;
    }
    return tails.length;
}
module.exports = {solve};
