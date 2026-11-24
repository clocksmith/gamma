'use strict';
function main(input) {
    const args = input.split(' ');
    const n = parseInt(args[0], 10);
    const x = parseInt(args[1], 10);
    const y = parseInt(args[2], 10);
    let d_obj = {};
    for (let i = 1; i < n; i++) {
        d_obj[i] = 0;
    }
    
    for (let i = 1; i < n; i++) {
        for (let j = i + 1; j < n + 1; j++) {
            if (j <= x || y <= i) {
                d_obj[j - i] += 1;
            } else if (i <= x && j <= y) {
                d_obj[Math.min(j - i, x - i + y - j + 1)] += 1;
            } else if (i <= x && j > y) {
                d_obj[x - i + j - y + 1] += 1;
            } else if (x < i < y && j < y) {
                d_obj[Math.min(j - i, i - x + y - j + 1)] += 1;
            } else if (x < i < y && j >= y) {
                d_obj[Math.min(j - i, i - x + j - y + 1)] += 1;
            }
        }
    }

    for (let i = 1; i < n; i++) {
        console.log(d_obj[i]);
    }
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));