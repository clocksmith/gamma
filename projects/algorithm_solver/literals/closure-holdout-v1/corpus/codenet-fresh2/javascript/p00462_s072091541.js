var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n").map(Number);
while(true){
var d=arr.shift();
if(d==0)break;
var n=arr.shift()-1;
var m=arr.shift();
var N=[0,d];
for(var i=0;i<n;i++){
   var x=arr.shift();
   N.push(x,x+d,x-d);
}
var M=[];
for(var i=0;i<m;i++)M.push(arr.shift());
N.sort(function(a,b){return a-b;});
M.sort(function(a,b){return a-b;});
var sum=0;
M.forEach(function(value){
   var min=Infinity;
   var L=0;
   var R=N.length-1;
   while(true){
      var i=Math.floor((L+R)/2);
      if(N[i]==value){
         min=Math.min(min,Math.abs(N[i]-value));
         break;
      }else if(N[i]>value){
         min=Math.min(min,Math.abs(N[i]-value));
         R=i-1;
      }else if(N[i]<value){
         min=Math.min(min,Math.abs(N[i]-value));
         L=i+1;
      }
      if(L>R){
         min=Math.min(min,Math.abs(N[i]-value));
         break;
      }
   }
   sum+=min;
});
console.log(sum);
}