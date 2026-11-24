var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var N=Arr.shift()-0;
var AB=(Arr.shift()).split(" ").map(Number);
var C=Arr.shift()-0;
var arr=[];
for(var i=0;i<N;i++){
   var v=Arr.shift()-0;
   arr.push(v);
}
arr.sort(function(a,b){return b-a;});
var ans=[];
var money=AB[0];
var cal=C;
for(var i=0;i<N;i++){
   money+=AB[1];
   cal+=arr[i];
   var v=cal/money;
   ans.push(v);
}
var max=Math.max.apply(null,ans);
console.log(Math.floor(max));