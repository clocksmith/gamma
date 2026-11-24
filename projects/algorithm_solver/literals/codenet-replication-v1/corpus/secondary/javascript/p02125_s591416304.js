var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
var n = arr.shift()-0;
var s = (n.toString(2) + "").split("").map(Number);
var sum = s.reduce((a,b)=>a+b); 
var l = (n.toString(2) + "").length - 1;
console.log(Math.max(sum,l));
