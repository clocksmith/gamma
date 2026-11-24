var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
for(var i=0;i<Arr.length;i=i+2){
var x=Arr[i];
var h=Arr[i+1];
if(x==0 && h==0)break;
var S=x*Math.sqrt(4*h*h+x*x)+x*x;
console.log(S.toFixed(5));
}