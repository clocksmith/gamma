'use strict';

function solve(nums, k, queries) {
    const n = nums.length;
    let size = 1;
    while (size < n) size *= 2;
    const identity = { product: 1 % k, counts: new Array(k).fill(0) };
    const tree = new Array(2 * size).fill(identity);
    function merge(left, right) {
        const counts = left.counts.slice();
        for (let r = 0; r < k; r++) {
            counts[left.product * r % k] += right.counts[r];
        }
        return { product: left.product * right.product % k, counts };
    }
    function leaf(value) {
        const counts = new Array(k).fill(0);
        counts[value % k] = 1;
        return { product: value % k, counts };
    }
    for (let i = 0; i < n; i++) tree[size + i] = leaf(nums[i]);
    for (let i = size - 1; i > 0; i--) tree[i] = merge(tree[2 * i], tree[2 * i + 1]);
    const answers = [];
    for (const [index, value, start, x] of queries) {
        let node = size + index;
        tree[node] = leaf(value);
        for (node = Math.floor(node / 2); node > 0; node = Math.floor(node / 2)) {
            tree[node] = merge(tree[2 * node], tree[2 * node + 1]);
        }
        let low = size + start;
        let high = size + n;
        let left = identity;
        let right = identity;
        while (low < high) {
            if (low % 2) left = merge(left, tree[low++]);
            if (high % 2) right = merge(tree[--high], right);
            low = Math.floor(low / 2);
            high = Math.floor(high / 2);
        }
        answers.push(merge(left, right).counts[x]);
    }
    return answers;
}
module.exports = { solve };
