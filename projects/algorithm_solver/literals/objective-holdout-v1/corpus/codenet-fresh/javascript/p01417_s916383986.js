var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var nm=arr.shift().split(" ").map(Number);
var n=nm[0];
var m=nm[1];
var all=[];
var loop=function (start,ary){
   if(ary.length==m)all.push(ary);
   else{
      for(var i=start;i<n;i++)loop(i+1,ary.concat(i));
   }
};
loop(0,[]);
var ab=[];
while(n--)ab.push(arr.shift().split(" ").map(Number));
var max=0;
all.forEach(function(v){
   var sum=0;
   while(true){
      if(v.length<=1)break;
      var a=v.shift();
      v.forEach(function(value){
         sum+=(ab[a][0]-ab[value][0])*(ab[a][0]-ab[value][0]);
         sum+=(ab[a][1]-ab[value][1])*(ab[a][1]-ab[value][1]);
         sum+=(ab[a][2]-ab[value][2])*(ab[a][2]-ab[value][2]);
      });
   }
   max=Math.max(max,sum);
});
console.log(max.toFixed(6));