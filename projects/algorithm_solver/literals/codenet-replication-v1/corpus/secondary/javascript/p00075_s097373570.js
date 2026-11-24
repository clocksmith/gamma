var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
Arr.forEach(function(v){
var arr=v.split(",").map(Number);
var d=arr[1]/Math.pow(arr[2],2);
if(d>=25)console.log(arr[0])
});