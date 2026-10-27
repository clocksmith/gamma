'use strict';

function solve(n, present, future, hierarchy, budget) {
    const children = Array.from({ length: n }, () => []);
    for (const [boss, employee] of hierarchy) children[boss - 1].push(employee - 1);
    const order = [0];
    for (let i = 0; i < order.length; i++) order.push(...children[order[i]]);
    const dp = new Array(n);
    function merge(left, right) {
        const result = new Array(budget + 1).fill(-Infinity);
        for (let a = 0; a <= budget; a++) {
            if (left[a] === -Infinity) continue;
            for (let b = 0; a + b <= budget; b++) {
                if (right[b] !== -Infinity) result[a + b] = Math.max(result[a + b], left[a] + right[b]);
            }
        }
        return result;
    }
    for (let i = n - 1; i >= 0; i--) {
        const u = order[i];
        let skip = new Array(budget + 1).fill(-Infinity);
        skip[0] = 0;
        let buy = skip.slice();
        for (const v of children[u]) {
            skip = merge(skip, dp[v][0]);
            buy = merge(buy, dp[v][1]);
        }
        dp[u] = [0, 1].map(parentBought => {
            const cost = parentBought ? Math.floor(present[u] / 2) : present[u];
            const result = skip.slice();
            for (let spent = cost; spent <= budget; spent++) {
                result[spent] = Math.max(result[spent], buy[spent - cost] + future[u] - cost);
            }
            return result;
        });
    }
    return Math.max(...dp[0][0]);
}

module.exports = { solve };
