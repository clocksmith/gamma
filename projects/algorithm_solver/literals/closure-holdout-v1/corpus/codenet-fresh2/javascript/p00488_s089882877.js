var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var lines = input.split('\n');

var p = []
var j = []
p[0] = Number(lines[0]);
p[1] = Number(lines[1]);
p[2] = Number(lines[2]);
j[0] = Number(lines[3]);
j[1] = Number(lines[4]);

console.log(Math.min.apply(null, p) + Math.min.apply(null, j) - 50)