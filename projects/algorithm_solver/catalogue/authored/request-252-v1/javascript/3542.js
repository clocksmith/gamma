'use strict';

function solve(nums) {
    const stack = [0];
    let operations = 0;
    for (const value of nums) {
        while (stack[stack.length - 1] > value) stack.pop();
        if (stack[stack.length - 1] < value) {
            stack.push(value);
            operations++;
        }
    }
    return operations;
}
module.exports = { solve };
