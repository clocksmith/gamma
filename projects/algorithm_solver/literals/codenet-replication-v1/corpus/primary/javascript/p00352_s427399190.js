var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split(" ").map(Number);
console.log((arr[0]+arr[1])/2);

