var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var [a,b]= input.trim().split(" ").map(Number);
console.log((4/3*Math.PI*b*b*b).toFixed(6));
