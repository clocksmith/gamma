var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
var arr=[];
for(var i=0;i<=100;i++)arr[i]=0;
var cnt=0;
Arr.forEach(function(v){
arr[v]++;
if(arr[v]>cnt)cnt=arr[v];
});
arr.forEach(function(v,i){
if(v==cnt)console.log(i);
});