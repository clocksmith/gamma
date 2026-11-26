"use strict"
function main(arg) {
    var s = arg.trim().split("\n")[0]
    if (s[2] === s[3] && s[4] === s[5]) {
        console.log('Yes')
    } else {
        console.log('No')
    }
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));