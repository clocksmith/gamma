function riffle(arr){
   var len=arr.length/2;
   var after=[];
   for(var i=0;i<len;i++)after.push(arr[i],arr[i+len]);
   return after;
}
 
function cut(arr,x){
   var a=arr.slice(0,x);
   var b=arr.slice(x,arr.length+1);
   return b.concat(a);
}
 
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
var a=2*Arr[0];
var card=[];
for(var i=0;i<a;i++)card[i]=i+1;
Arr.shift();
var AL=Arr.shift();
 
for(i=0;i<AL;i++){
   if(Arr[i]==0)card=riffle(card);
   if(Arr[i]>0)card=cut(card,Arr[i]);
}
 
card.forEach(function(v){console.log(v);});