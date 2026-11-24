var a = require('fs').readFileSync('/dev/stdin', 'utf8').trim().split(" ");
console.log(Math.pow(2,Math.floor(Math.log(a)/Math.log(2))))
