var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var NL=arr.shift().split(" ").map(Number);
var N=NL[0];
var L=NL[1];
arr.length=N;
arr=arr.map(Number);
var s=arr.map(function(v,i){return [v,i];});
s.sort(function(a,b){return b[0]-a[0];});
var life=[];
s.forEach(function(v){
   var i=v[1];
   if(i==0){
      if(arr[i]>arr[i+1])life[i]=L-arr[i];
      else life[i]=life[i+1]+L-arr[i];
   }else if(i==arr.length-1){
      if(arr[i]>arr[i-1])life[i]=L-arr[i];
      else life[i]=life[i-1]+L-arr[i];
   }else{
      if(arr[i]>arr[i-1] && arr[i]>arr[i+1])life[i]=L-arr[i];
      else if(arr[i]>arr[i-1] && arr[i]<arr[i+1])life[i]=life[i+1]+L-arr[i];
      else if(arr[i]<arr[i-1] && arr[i]>arr[i+1])life[i]=life[i-1]+L-arr[i];
      else if(arr[i]<arr[i-1] && arr[i]<arr[i+1])life[i]=Math.max(life[i-1],life[i+1])+L-arr[i];
   }
});
var ans=0;
life.forEach(function(v){
   ans=Math.max(ans,v);
});
console.log(ans);