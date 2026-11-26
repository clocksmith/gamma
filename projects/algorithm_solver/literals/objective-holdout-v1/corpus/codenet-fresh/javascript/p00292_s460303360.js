var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
Arr.shift();
Arr.forEach(function(v,i){
var arr=Arr[i].split(" ").map(Number);
var a=arr[0]%arr[1];
if(a==0)a=arr[1];
console.log(a);
});