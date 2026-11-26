var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var NQ=(Arr.shift()).split(" ").map(Number);
var N=NQ[0];
var Q=NQ[1];
var str="kogakubu10gokan";
for(var i=0;i<N;i++){
   var arr=Arr[i].split(" ");
   var a=arr[0]-0;
   if(a<=Q)str=arr[1];
}
console.log(str);