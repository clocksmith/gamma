var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr= input.trim().split("\n");
var [h,w]=arr[0].split(" ").map(Number);
var [a,b]=arr[1].split(" ").map(Number);
var x=Math.floor(h/a);
var y=Math.floor(w/b);
console.log(h*w-x*a*y*b);
