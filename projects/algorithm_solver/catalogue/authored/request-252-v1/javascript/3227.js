'use strict';

function solve(s) {
    for (const char of s) {
        if ('aeiou'.includes(char)) return true;
    }
    return false;
}

module.exports = { solve };
