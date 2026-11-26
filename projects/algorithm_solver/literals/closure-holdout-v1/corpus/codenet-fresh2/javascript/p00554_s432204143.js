var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var nm = arr.shift().split(" ").map(Number);
var n = nm[0];
var max = 0;
arr = arr.map(function(v){
   var ab = v.split(" ").map(Number);
   max = Math.max(max, n - ab[0]);
   return Math.max(0, n - ab[0]);
});
var sum = arr.reduce(function(a,b){
   return a+b;
});
console.log(sum-max);