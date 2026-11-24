var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
Arr.shift();
var max=0;
var arr=[];
Arr.forEach(function(v){
var a=(v.split(" "))[0]-0;
var b=(v.split(" "))[1]-0;
   if(max==b)arr.push(a);
   if(max<b){
      max=b;
      arr=[a];
   }
});
arr.sort(function(a,b){return a-b;});
console.log(arr[0]+" "+max);