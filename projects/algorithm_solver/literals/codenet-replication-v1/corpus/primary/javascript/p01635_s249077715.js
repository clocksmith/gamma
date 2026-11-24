var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var A=arr.shift().split(" ").map(Number);
var B=arr.shift().split("+");
var sum=0;
B.forEach(function(v){
   var num=v.replace(/n\^/g,"")-0;
   sum+=Math.pow(A[0],num);
});
sum=sum*A[1];
if(sum>1000000000)sum="TLE";
console.log(sum);