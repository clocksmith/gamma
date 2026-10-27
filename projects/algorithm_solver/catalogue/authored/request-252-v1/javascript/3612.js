'use strict';

function solve(s) {
    let result = [];
    for (const char of s) {
        if (char === '*') result.pop();
        else if (char === '#') result = result.concat(result);
        else if (char === '%') result.reverse();
        else result.push(char);
    }
    return result.join('');
}
module.exports = { solve };
