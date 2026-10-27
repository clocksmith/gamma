'use strict';

function solve(s) {
    const stack = [];
    for (const char of s) {
        const difference = stack.length ? Math.abs(char.charCodeAt(0) - stack[stack.length - 1].charCodeAt(0)) : 0;
        if (difference === 1 || difference === 25) stack.pop();
        else stack.push(char);
    }
    return stack.join('');
}
module.exports = { solve };
